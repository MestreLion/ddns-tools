#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# sendmail - Send email using ssmtp's settings
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

import os.path as osp
import smtplib
import ConfigParser
import StringIO
import socket
import logging

from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

# TODO: make this a class with all attributes with default values
def ssmtp_config():
    def addsection(filename):
        config = StringIO.StringIO()
        config.write('[default]\n')
        try:
            with open(filename) as f:
                config.write(f.read())
        except IOError:
            pass
        config.seek(0)
        return config

    cp = ConfigParser.ConfigParser()
    # For Python 3, use cp.read_string() and modify addsection() accordingly
    cp.readfp(addsection('/etc/ssmtp/ssmtp.conf'))
    cp.readfp(addsection(osp.expanduser('~/.config/ssmtp/ssmtp.conf')))

    config = {}
    for item in cp.items('default'):
        config[item[0]] = item[1]

    return config


def sendmail(sender, recipients, subject="", text="", attachments=[],
             debug=False):

    # read and handle ssmtp's settings
    # TODO: add **kwargs to override ssmtp settings
    # TODO: emulate the heuristics of RewriteDomain, FromLineOverride, etc
    ssmtp = ssmtp_config()
    mailhub  = ssmtp.get('mailhub', 'localhost')
    usetls   = ssmtp.get('usetls', 'no').lower() == 'yes'
    hostname = ssmtp.get('hostname', socket.gethostname())
    authuser = ssmtp.get('authuser', '')
    authpass = ssmtp.get('authpass', '')

    # handle arguments
    if isinstance(attachments, basestring):
        attachments = [attachments]

    if isinstance(recipients, basestring):
        recipients = [recipients]

    if not len(sender.split('@', 1)) == 2:
        sender = "%s@%s" % (sender, hostname)

    # Create the container (outer) email message.
    msg = MIMEMultipart()
    msg['From']    = sender
    msg['To']      = ', '.join(recipients)
    msg['Subject'] = subject

    # Add body
    msg.attach(MIMEText(text))

    # Add attachments
    for attachment in attachments:
        with open(attachment) as fp:
            part = MIMEApplication(fp.read())
            part.add_header('Content-Disposition', 'attachment',
                              filename=osp.basename(attachment))
            msg.attach(part)

    # Connect
    if usetls:
        smtp = smtplib.SMTP_SSL(mailhub)
    else:
        smtp = smtplib.SMTP(mailhub)

    try:
        smtp.set_debuglevel(1 if debug else 0)
        # Authenticate
        if authuser and authpass:
            smtp.login(authuser, authpass)
        # Send
        smtp.sendmail(sender, recipients, msg.as_string())
    finally:
        smtp.quit()


if __name__ == '__main__':

    sendmail('you@example.com',
             'test@rodrigosilva.com',
             'Example subject',
             'Example text body',
             ['/etc/ssmtp/ssmtp.conf'],
             )