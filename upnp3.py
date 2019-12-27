#!/usr/bin/env python3
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

import requests


class UpnpError(Exception):
    pass


def external_ip():

    def search(regex, text):
        match = regex.search(text)
        if match:
            return match.groups()[0].strip()

    def get_tag(tag, text, alltags=False):
        r = re.compile(fr"<{tag}>(.+?)</{tag}>", re.IGNORECASE | re.DOTALL)
        if alltags:
            return r.findall(text)
        else:
            return search(r, text)

    def sockdata(data):
        return bytes(re.sub('[\t ]*\r?\n[\t ]*', '\r\n', data.lstrip()), 'utf-8')

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    sock.settimeout(10)

    data = """
        M-SEARCH * HTTP/1.1
        HOST: 239.255.255.250:1900
        MAN: "ssdp:discover"
        MX: 5
        ST: ssdp:all

    """
    sock.sendto(sockdata(data), ("239.255.255.250", 1900))

    endpoints = []
    while True:
        try:
            data = sock.recv(2048).decode()
        except socket.timeout:
            if endpoints:
                break
            raise UpnpError("No UPnP gateway found")

        service  = search(re.compile(r"^ST:\s*([^\s]+WAN(IP|PPP)Connection:\d+)\s*$",
                                     re.IGNORECASE | re.MULTILINE), data)
        location = search(re.compile(r"^Location:\s*([^\s]+)\s*$",
                                     re.IGNORECASE | re.MULTILINE), data)

        if location and service:
            endpoints.append((location, service))
            if ':WANIPConnection:' in service:
                break

    controlURL = ""
    for location, service in endpoints:
        data = requests.get(location).text
        URLBase = get_tag("URLBase", data) or ("http://" + requests.utils.urlparse(location).netloc)
        for serv in get_tag("service", data, alltags=True):
            if get_tag("serviceType", serv) == service:
                controlURL = get_tag("ControlURL", serv)
                break
        if controlURL:
            break
    else:
        raise UpnpError(f"No controlURL found for server: {location}")

    url = requests.compat.urljoin(URLBase, controlURL)
    action = "GetExternalIPAddress"
    headers = {
        'content-type': 'text/xml; charset="utf-8"',
        'SOAPACTION': f'"{service}#{action}"',
    }
    data = f"""<?xml version="1.0"?>
    <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"
        s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
    <s:Body>
    <u:{action} xmlns:u="{service}"></u:{action}>
    </s:Body>
    </s:Envelope>"""
    data = requests.post(url, headers=headers, data=data).text
    ip = data and get_tag("NewExternalIPAddress", data)
    if not ip:
        raise UpnpError("Couldn't get external IP address!")

    return ip


USAGE = """Find external IP address via UPnP
Usage: python3 upnp3.py
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
