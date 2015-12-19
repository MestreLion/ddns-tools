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
try:
    # Debian/Ubuntu: python-keyring
    import keyring
except ImportError:
    keyring = None


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

        log.debug("Opening '%s'", url)

        if username and password:
            log.debug("Using HTTP Basic Authentication")
            auth = ("%s:%s" % (username, password)).encode("UTF-8")
            headers = {'Authorization': b'Basic ' + base64.b64encode(auth)}
            req = urllib2.Request(url, headers=headers)
        else:
            req = url

        if postdata:
            return self._opener.open(req, urllib.urlencode(postdata))
        else:
            return self._opener.open(req)


def main(argv=None):
    args = parse_args(argv)
    logging.basicConfig(level=args.loglevel,
                        format='%(asctime)s\t%(levelname)-8s\t%(message)s',
                        )#filename=os.path.join(xdg.xdg_cache_home,
                        #                      '%s.log' % myname))
    log.debug(args)
    config = read_config(args)

    username  = args.username  or config['username']  or USERNAME
    password  = args.password  or config['password']  or PASSWORD
    hostnames = args.hostnames or config['hostnames'] or HOSTNAMES

    if not (username or password):
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

    body = res.read()
    for line in body.split('\n'):
        log.info(line)

    if body.startswith("badauth"):
        log.error("Bad authentication, check your login and password")
        return -1


def read_config(args):
    config = os.path.join(xdg.save_config_path(myname), "%s.conf" % myname)
    auth   = os.path.join(xdg.save_config_path(myname), "%s.auth.conf" % myname)

    username = ""
    password = ""
    hostnames = []

    # Read
    if keyring:
        log.debug("Reading credentials from keyring")
        try:
            username, password = (keyring.get_password(myname, '').split('\n')
                                  + ['\n'])[:2]
        except IOError as e:
            log.error(e)
        except AttributeError as e:
            # not found in keyring
            pass
    else:
        log.debug("Reading credentials from '%s'", auth)
        try:
            with open(config, 'r') as fd:
                username, password = (fd.read().splitlines() + ['\n'])[:2]
        except IOError as e:
            log.warn(e)

    log.debug("Reading hostnames from '%s'" % config)
    try:
        with open(config, 'r') as fd:
            for line in fd:
                hostnames.append(line.strip())
    except IOError as e:
        log.warn(e)

    # Save
    if args.username or args.password:
        log.info("Saving credentials")
        if keyring:
            log.debug("Saving credentials to keyring")
            keyring.set_password(myname, '',
                                 '%s\n%s' % (args.username or username,
                                             args.password or password,))
        else:
            log.debug("Saving credentials to '%s'", auth)
            try:
                with open(auth, 'w') as fd:
                    fd.write("%s\n%s\n" % (args.username or username,
                                           args.password or password,))
                os.chmod(auth, 0600)
            except IOError as e:
                log.error(e)

    if args.hostnames:
        log.info("Saving hostnames")
        try:
            log.debug("Saving hostnames to '%s'", config)
            with open(config, 'w') as fd:
                for hostname in args.hostnames:
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
                       help="Verbose mode, output extra info.")

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
