#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2015 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. See <http://www.gnu.org/licenses/gpl.html>

"""
    No-IP Dynamic DNS Update Client
"""

USERNAME = ""
PASSWORD = ""
HOSTNAMES = []
SERVER = "https://dynupdate.no-ip.com/nic/update"


import sys
import os.path
import logging
import argparse
import xdg.BaseDirectory as xdg
import urllib
import urllib2
import base64
import cStringIO


myname = os.path.basename(os.path.splitext(__file__)[0])
log = logging.getLogger(myname)


class HttpAuth(object):
    """Simplified version of HttpBot with HTTP Basic Authentication"""
    def __init__(self, debug=False):
        hh  = urllib2.HTTPHandler( debuglevel=1 if debug else 0)
        hsh = urllib2.HTTPSHandler(debuglevel=1 if debug else 0)
        self._opener = urllib2.build_opener(hh, hsh)

    def get(self, url, querydata=None, postdata=None, username="", password=""):
        if querydata:
            url = "%s?%s" % (url, urllib.urlencode(querydata))

        if postdata:
            data = urllib.urlencode(postdata)
        else:
            data = None

        log.debug("Opening '%s'", url)

        if username and password:
            log.debug("Using HTTP Basic Authentication")
            auth = ("%s:%s" % (username, password)).encode("UTF-8")
            headers = {'Authorization': b'Basic ' + base64.b64encode(auth)}
            req = urllib2.Request(url, headers=headers)
        else:
            req = url

        # Redirect stdout so urllib's debug data gets properly logged
        stdout_ = sys.stdout
        stream = cStringIO.StringIO()
        sys.stdout = stream

        # Open the URL
        res = self._opener.open(req, data)

        # Restore stdout and log output, if any
        sys.stdout = stdout_
        output = stream.getvalue().strip()
        if output:
            for line in output.split('\n'):
                log.debug(line)

        return res


def main(argv=None):
    args = parse_args(argv)
    logging.basicConfig(level=args.loglevel,
                        format='%(asctime)s\t%(levelname)-8s\t%(message)s',
                        filename=os.path.join(xdg.xdg_cache_home,
                                              '%s.log' % myname))
    log.debug(args)
    config = read_config(args)

    username  = args.username  or config['username']  or USERNAME
    password  = args.password  or config['password']  or PASSWORD
    hostnames = args.hostnames or config['hostnames'] or HOSTNAMES

    if not (username and password):
        log.error("Missing credentials."
                  " Set them up once with --username and --password")
        return -1

    if not hostnames:
        log.error("No hosts to update."
                  " Set them up once using command line arguments")
        return -1

    try:
        http = HttpAuth(debug=args.debug)
        res = http.get(SERVER,
                       querydata={'hostname': ",".join(hostnames)},
                       username=username,
                       password=password)
    except urllib2.HTTPError as e:
        if e.code != 401:  # Unauthorized
            raise
        log.error("Unauthorized, check your login and password")
        return -1

    body = res.read().strip()
    for line in body.split('\n'):
        log.info(line)

    if body.startswith("badauth"):
        log.error("Bad authentication, check your login and password")
        return -1


def read_config(args):
    config = os.path.join(xdg.save_config_path(myname), "%s.conf" % myname)

    username = ""
    password = ""
    hostnames = []

    # Read
    log.debug("Reading settings from '%s'", config)
    try:
        with open(config, 'r') as fd:
            username, password = fd.readline().strip().split('\t')
            for line in fd:
                hostnames.append(line.strip())
    except IOError as e:
        log.warn(e)
    except ValueError as e:
        log.error("Error in config file, check credentials at '%s'", config)

    # Save
    if args.username or args.password or args.hostnames:
        log.info("Saving settings to '%s'", config)
        try:
            with open(config, 'w') as fd:
                fd.write("%s\t%s\n" % (args.username or username,
                                       args.password or password,))
                for hostname in (args.hostnames or hostnames):
                    fd.write("%s\n" % hostname)
            os.chmod(config, 0600)
        except IOError as e:
            log.error(e)

    return dict(username=username,
                password=password,
                hostnames=hostnames)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__)

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-q', '--quiet',
                       dest='loglevel',
                       const=logging.WARNING,
                       default=logging.INFO,
                       action="store_const",
                       help="Suppress informative messages.")

    group.add_argument('-v', '--verbose',
                       dest='loglevel',
                       const=logging.DEBUG,
                       action="store_const",
                       help="Verbose mode, output extra info."
                        " This will disclose your username and password"
                        " in the log file, so use with care!")

    group = parser.add_argument_group("Authentication Options")
    group.add_argument('-u', '--username', help="Account username or email")
    group.add_argument('-p', '--password', help="Account password")

    parser.add_argument(nargs="*", dest='hostnames',
                        help="Hostnames to update."
                            " Will also be saved in config file for future runs.")

    args = parser.parse_args(argv)
    args.debug = args.loglevel == logging.DEBUG

    return args




if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        log.critical(e, exc_info=True)
        sys.exit(1)
    except KeyboardInterrupt:
        pass
