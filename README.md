Tools for Dynamic DNS
=====================

noip
----

Updates your hostnames at [NoIP](http://noip.com) DDNS provider to the IP seen by the NoIP service.


dyndns-weblogin
---------------

Logs in to dyndns.com website, suitable for cron usage, to meet dyndns' (absurd) monthly login policy.


dyndns-update
-------------

Now that dyndns.com cancelled all free domains, I'm rolling out my own solution: announcing the external public IP myself. The prefix `dyndns-` is actually a misnomer, since it does not use any dyndns.com service. Actually, it partially *replaces* DDNS features.

External IP is obtained by querying the Gateway/Router via UPnP. If it has changed since previous run, sends an email using your current [sSMTP](http://packages.qa.debian.org/s/ssmtp.html) settings and updates records at NoIP.

In the future actions might be expanded to include more DDNS providers like [DNS-O-Matic](http://dnsomatic.com), update an external website to act similar to [WhatIsMyIp](http://whatismyip.com), or update domain DNS records in registars like [GoDaddy](http://godaddy.com).

Who needs the insecure, non-HTTPS `inadyn` or `ddclient` when you can have the half-baked, home-made, craptastic `dyndns-update` in your `{ana,}cron` ? :)

---

Contributing
------------

Patches are welcome! Fork, hack, request pull!

If you find a bug or have any enhancement request, please open a [new issue](https://github.com/MestreLion/ddns-tools/issues/new)


Written by
----------

Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>

Licenses and Copyright
----------------------

Copyright (C) 2012 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>.

License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.

This is free software: you are free to change and redistribute it.

There is NO WARRANTY, to the extent permitted by law.
