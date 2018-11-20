# Copyright (C) 2018 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>
"""
Python 2/3 urllib compatibility wrapper
"""
try:
    # Python 3
    from urllib.request import build_opener, Request
    from urllib.parse   import urlparse, urljoin

except ImportError:
    # Python 2
    from urllib2  import build_opener, Request  # @UnusedImport
    from urlparse import urlparse, urljoin      # @UnusedImport
