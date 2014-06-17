Tools for Dynamic DNS
=====================

dyndns-weblogin
---------------

Logs in to dyndns.com website, suitable for cron usage, to meet dyndns' (absurd) monthly login policy.


dyndns-update
-------------

Now that dyndns.com cancelled all free domains, I'm rolling out my own solution: announcing the external public IP myself. The prefix `dyndns-` is actually a misnomer, since it does not use any dyndns.com service. Actually, it partially *replaces* DDNS features.

External IP is obtained by querying the Gateway/Router via UPnP.

Notification is currently via email only. But in the future it can update DDNS services like [NoIP](http://noip.com) or [DNS-O-Matic](http://dnsomatic.com), or update an external website to act similar to [WhatIsMyIp](http://whatismyip.com).

Who needs the insecure, non-HTTPS `inadyn` or `ddclient` when you can have the half-baked, home-made, craptastic `dyndns-update` in your `{ana,}cron` ? :)