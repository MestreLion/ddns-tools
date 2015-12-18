#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# dyndns-update - Find external IP and make it visible
#
#    Copyright (C) 2013 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
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
#
# "dyndns" is actually a misnomer: it has nothing to do with DynDNS.com
# "Make the IP it visible" currently means "email it". Crude, but it works


import sys
import os.path as osp
import logging
import argparse
import xdg.BaseDirectory as xdg

import sendmail
import upnp

myname = __name__
logger = logging.getLogger(myname)


def main(args):
    config = read_config(args)
    recipients = args.recipients or config['recipients']
    if not recipients:
        logger.error("Recipients list is empty. Set them up once using command line arguments")
        return -1

    ipfile = osp.join(xdg.save_config_path(myname), 'ip')

    try:
        logger.debug("Reading previous IP file: %s", ipfile)
        with open(ipfile) as f:
            oldip = f.read().strip()
    except IOError as e:
        logger.warn(e)
        oldip = ""

    try:
        newip = upnp.external_ip()
    except (upnp.UpnpError, upnp.socket.error) as e:
        logger.error(e)
        return

    if newip == oldip:
        logger.info("IP is still %s", oldip)
        if not args.force:
            return
    else:
        logger.info("IP changed from %s to %s", oldip, newip)
        logger.debug("Saving new IP file", ipfile)
        try:
            with open(ipfile, 'w') as f:
                f.write('%s\n' % newip)
        except IOError as e:
            logger.error(e)

    try:
        logger.info("Sending email")
        sendmail.sendmail(myname,
                          recipients,
                          "External public IP changed to %s" % newip,
                          newip,
                          debug=args.debug,)
    except (sendmail.smtplib.SMTPException, sendmail.socket.gaierror) as e:
        logger.error(e)


def read_config(args):
    config = osp.join(xdg.save_config_path(myname), "%s.conf" % myname)

    # Load
    logger.debug("Reading recipients list from '%s'" % config)
    recipients = []
    try:
        with open(config, 'r') as fd:
            for line in fd:
                recipients.append(line.strip())
    except IOError as e:
        logger.warn(e)

    # Save
    if args.recipients:
        logger.info("Saving recipients to config file")
        try:
            with open(config, 'w') as fd:
                for recipient in args.recipients:
                    fd.write("%s\n" % recipient)
        except IOError as e:
            logger.error(e)

    return dict(recipients=recipients)


def parseargs(args=None):
    parser = argparse.ArgumentParser(
        description="Login at DynDNS website to prevent account deletion.",)

    loglevels = ['debug', 'info', 'warn', 'error', 'critical']
    logdefault = 'info'
    parser.add_argument('--loglevel', '-l', dest='loglevel',
                        default=logdefault, choices=loglevels,
                        help="Set logging level, default is '%s'" % logdefault)

    parser.add_argument('--force', '-f', dest='force',
                        default=False,
                        action='store_true',
                        help='Force an update even if IP has not changed since last run.')

    parser.add_argument(nargs="*", dest='recipients',
                        help="Email recipients. Will also be saved in config file for future runs.")

    return parser.parse_args(args)

if __name__ == '__main__':
    myname = osp.basename(osp.splitext(__file__)[0])
    logfile = osp.join(xdg.xdg_cache_home, '%s.log' % myname)

    args = parseargs()
    args.debug = args.loglevel=='debug'

    logging.basicConfig(level=getattr(logging, args.loglevel.upper(), None),
                        format='%(asctime)s\t%(levelname)-8s\t%(message)s',
                        filename=logfile)

    try:
        sys.exit(main(args))
    except Exception as e:
        logger.critical(e, exc_info=True)
        sys.exit(1)
