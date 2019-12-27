#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# upnp - Find external IP address querying NAT Router/Gateway via UPnP
#
#    Copyright (C) 2014 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
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

# Inspired by Nikos Fotoulis public domain code

import sys
import re
import socket

import urllib23


class UpnpError(Exception):
    pass


def external_ip():

    def search(regex, text):
        match = regex.search(text)
        if match:
            return match.groups()[0].strip()

    def get_tag(tag, text, alltags=False):
        r = re.compile(r"<%s>(.+?)</%s>" % (tag, tag), re.IGNORECASE | re.DOTALL)
        if alltags:
            return r.findall(text)
        else:
            return search(r, text)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    sock.settimeout(10)

    data = 'M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: "ssdp:discover"\r\nMX: 5\r\nST: ssdp:all\r\n\r\n'
    sock.sendto(data, ("239.255.255.250", 1900))

    while True:
        try:
            data = sock.recv(2048)
        except socket.timeout:
            raise UpnpError("No UPnP gateway found")

        service  = search(re.compile(r"^ST:\s*([^\s]+WAN(IP|PPP)Connection:\d+)\s*$",
                                     re.IGNORECASE | re.MULTILINE), data)
        location = search(re.compile(r"^Location:\s*([^\s]+)\s*$",
                                     re.IGNORECASE | re.MULTILINE), data)

        if location and service:
            break

    data = urllib23.build_opener().open(location).read()
    URLBase = get_tag("URLBase", data) or "http://%s" % urllib23.urlparse(location).netloc
    for serv in get_tag("service", data, alltags=True):
        if get_tag("serviceType", serv) == service:
            controlURL = get_tag("ControlURL", serv)
            break
    else:
        raise UpnpError("No controlURL found for server: %s" % location)

    url = urllib23.urljoin(URLBase, controlURL)
    action = "GetExternalIPAddress"
    data = """<?xml version="1.0"?>
    <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"
        s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
    <s:Body>
    <u:%s xmlns:u="%s"></u:%s>
    </s:Body>
    </s:Envelope>""" % (action, service, action)

    req = urllib23.Request(url)
    req.add_header('content-type', 'text/xml; charset="utf-8"')
    req.add_header('SOAPACTION', '"%s#%s"' % (service, action))
    req.add_data(data)
    data = urllib23.build_opener().open(req).read()
    ip = data and get_tag("NewExternalIPAddress", data)
    if not ip:
        raise UpnpError("Couldn't get external IP address!")

    return ip


USAGE = """Find external IP address via UPnP
Usage: python upnp.py
"""
if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(USAGE)
        sys.exit()

    try:
        print(external_ip())
        sys.exit(0)
    except Exception as e:
        print(e)
        sys.exit(1)
