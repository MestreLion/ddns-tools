#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# dyndns-weblogin - Login at DynDNS website to prevent account deletion
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

# References:
# http://forums.redflagdeals.com/dyndns-free-account-policy-changes-1336819/2/#post16855638
# https://github.com/ntrrgc/dyndns-bot
# https://github.com/illusori/dyndns-login-cron
# https://github.com/flurischt/DynDNS

DYNDNS_USERNAME = ""
DYNDNS_PASSWORD = ""

import sys
import os.path as osp
import logging
import argparse
import time
import datetime
import random
import xdg.BaseDirectory as xdg

import sendmail

try:
    import selenium.webdriver, selenium.common.exceptions
    try:
        import pyvirtualdisplay
    except ImportError:
        pyvirtualdisplay = None
except ImportError:
    pyvirtualdisplay = None
    selenium = None


logger = logging.getLogger(__name__)
myname = __name__

def read_config(save=False, username=None, password=None):
    config = osp.join(xdg.save_config_path(myname), "%s.conf" % myname)
    if save:
        with open(config, 'w') as fd:
            fd.write("%s\n%s\n" % (username, password))
    else:
        try:
            with open(config, 'r') as fd:
                username = fd.readline().strip('\n')
                password = fd.readline().strip('\n')
        except IOError:
            logger.warn("Could not read config file. Use --save to set one")

    return dict(username=username,
                password=password)


def login(username, password, visible=False, debug=False):
    loginurl = "https://account.dyn.com/entrance"
    success = False
    display = None
    driver = None

    try:
        if pyvirtualdisplay and not visible:
            logger.info("using pyVirtualDisplay")
            display = pyvirtualdisplay.Display(visible=False, size=(1280, 720))
            display.start()

        if selenium:
            try:
                driver = selenium.webdriver.Firefox()
                logger.info("using selenium webdriver for Firefox")
            except selenium.common.exceptions.WebDriverException:
                logger.warn("Firefox not available, reverting to manual parsing")
                if debug:
                    logger.debug("selenium traceback:", exc_info=True)

        if driver:

            driver.get(loginurl)

            # find the fields
            form = driver.find_element_by_xpath("//form[starts-with(@id, 'login')]")
            input_username = form.find_element_by_xpath("//input[@name='username']")
            input_password = form.find_element_by_xpath("//input[@name='password']")
            input_submit   = form.find_element_by_xpath("//input[@name='submit']")

            # alternate way 1:
            #input_username = driver.find_element_by_css_selector('#loginbox input[name="username"]')
            #input_password = driver.find_element_by_css_selector('#loginbox input[name="password"]')
            #input_submit   = driver.find_element_by_css_selector('#loginbox input[name="submit"]')

            # alternate way 2:
            #input_username = driver.find_element_by_xpath(
            #    "//input[starts-with(@id, 'login') and contains(@id, 'username')]")
            #input_password = driver.find_element_by_xpath(
            #    "//input[starts-with(@id, 'login') and contains(@id, 'password')]")
            #input_submit   = driver.find_element_by_xpath(
            #    "//input[starts-with(@id, 'login') and contains(@id, 'submit')]")

            # fill data
            input_username.send_keys(username)
            input_password.send_keys(password)

            # submit
            logger.info("page loaded, logging in")
            time.sleep(random.randint(1, 5))  #
            input_submit.click()  # or input_password.submit() or form.submit()

            # wait for page to load completely and take a screenshot
            logger.info("saving screenshot as %s", screenshot)
            time.sleep(5)  # 5 is arbitrary, possibly too big, and maybe useless
            driver.get_screenshot_as_file(screenshot)

            # Test login success
            success = ("My Dyn Account" in driver.title or
                       "Log Out" in driver.page_source)

        else:
            #TODO: try manual parsing and sending with urllib2
            logger.warn("manual parsing not implemented yet")

    finally:
        if driver:  driver.quit()
        if display: display.stop()

    return success


def parseargs(args=None):
    parser = argparse.ArgumentParser(
        description="Login at DynDNS website to prevent account deletion.",)

    loglevels = ['debug', 'info', 'warn', 'error', 'critical']
    logdefault = 'info'
    parser.add_argument('--loglevel', '-l', dest='loglevel',
                        default=logdefault, choices=loglevels,
                        help="set logging level, default is '%s'" % logdefault)

    parser.add_argument('--show-window', '-w', dest='visible',
                        default=False,
                        action='store_true',
                        help='show browser window. Default is invisible window')

    parser.add_argument('--username', '-u', dest='username',
                        help="Account username, usually an email address")

    parser.add_argument('--password', '-p', dest='password',
                        help="Account password")

    parser.add_argument('--save', '-s', dest='save',
                        default=False,
                        action='store_true',
                        help="Saves the given username and password")

    return parser.parse_args(args)

if __name__ == '__main__':
    myname = osp.basename(osp.splitext(__file__)[0])
    screenshot = osp.join(xdg.xdg_cache_home, "%s_%s.png" % (myname,
                          datetime.datetime.now().strftime('%Y%m%d%H%M%S')))
    logfile = osp.join(xdg.xdg_cache_home, '%s.log' % myname)

    args = parseargs()
    debug = args.loglevel=='debug'

    logging.basicConfig(level=getattr(logging, args.loglevel.upper(), None),
                        format='%(asctime)s\t%(levelname)s\t%(name)s\t%(message)s',
                        filename=logfile)

    config = read_config(args.save, args.username, args.password)

    username = args.username or config['username'] or DYNDNS_USERNAME
    password = args.password or config['password'] or DYNDNS_PASSWORD

    if not (username and password):
        logger.critical("Username or Password are blank, aborting.")
        sys.exit(1)

    try:
        success = login(username, password, args.visible, debug)

        logger.info("emailing result")
        try:
            # process = subprocess.Popen(
            #     ['echo "login success" | mail -s "dyndns login success" YOUREMAIL@DOMAIN.TLD'],
            #     shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # stdout, stderr = process.communicate()
            message = "Dyndns automatic web login %s" % ("successful" if success
                                                         else "FAILED!")
            attachments = []
            if osp.isfile(screenshot):
                attachments.append(screenshot)

            if not success:
                attachments.append(logfile)

            sendmail.sendmail(myname,
                              username,
                              message,
                              message,
                              attachments,
                              debug=debug,)
        except sendmail.smtplib.SMTPException as e:
            logger.error(e)
        except Exception as e:
            logger.error(e, exc_info=True)

        sys.exit(0 if success else 1)

    except Exception as e:
        logger.critical(e, exc_info=True)
        sys.exit(1)
