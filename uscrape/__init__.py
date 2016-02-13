# coding: utf-8
from __future__ import print_function
import re
import sys
import time
import requests
import lxml.html

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
try:
    from urllib.parse import urlparse, unquote, quote
except ImportError:
    from urlparse import urlparse
    from urllib import unquote, quote


def make_tree(url, data, encoding=None):
    """Build lxml tree."""
    s = StringIO(data)
    parser = lxml.html.HTMLParser(encoding=encoding)
    doc = lxml.html.parse(s, parser=parser)
    html = doc.getroot()
    html.make_links_absolute(url)
    return html


def to_text(elem):
    t = [elem.text or '']
    for e in elem.getchildren():
        t.append(to_text(e))
    t.append(elem.tail or '')
    return ' '.join(t)


class UrlOpener(object):
    def __init__(self, sleep_time=1):
        self.client = requests.session()
        self.sleep_time = sleep_time

    def get_url(self, url, raw=False):
        """
        Fetch URL via GET request.

        Handles speed limit (1 request / self.sleep_time)
        Handles incremental backoff with 10 retries.
        """
        waittime = getattr(self, 'last_fetch', 0) + self.sleep_time - time.time()
        if waittime > 0:
            time.sleep(waittime)

        resp = None

        # begin download
        print('Fetching...', url, file=sys.stderr)
        n = 0
        # adaptive timeout
        try:
            timeout = max(self.__last_fetch_took + 5, 30)
        except:
            timeout = 30
        while True:
            try:
                request_start = time.time()
                resp = self.client.get(url, timeout=timeout)
                resp.raise_for_status()
                if not raw:
                    # detect charset
                    content_type = resp.headers.get('content-type')
                    m = re.search(';\s*charset=(.*)\s*$', content_type, re.I)
                    charset = None
                    if m:
                        charset = m.group(1).strip()
                    else:
                        charset = 'utf-8'
                    try:
                        content = resp.content.decode(charset).encode('utf-8')
                    except:
                        content = resp.content
                else:
                    content = resp.content
                self.last_response = resp
                self.__last_fetch_took = time.time() - request_start
                break
            except Exception as e:
                print(e)
                import traceback
                traceback.print_exc()

                if e.response and e.response.status_code in (404, 403):
                    return ''

                if n < 10:  # FIXME: was 5
                    n += 1
                    timeout = 30 * (n + 1)
                    time.sleep(5)
                    print('Retry %s ...' % n, file=sys.stderr)
                else:
                    raise
        # end download

        self.last_fetch = time.time()
        return content


class Url:
    """URL parsing class for easily changing URL parameters."""

    def __init__(self, u):
        url = urlparse(u)
        self.scheme = url[0]
        self.hostname = url[1]
        self.path = url[2]
        try:
            args = [part.split('=') for part in url[4].split('&') if part]
            self.args = dict([(unquote(k), unquote(v)) for k, v in args])
        except:
            print(u)
            raise
        self.fragment = url[5]

    def domain():
        def fget(self):
            return '.'.join(self.hostname.rstrip('.').split('.')[-2:])
        return locals()
    domain = property(**domain())

    def query():
        def fget(self):
            args = ['%s=%s' % (quote(k), quote(v)) for k, v in self.args.items()]
            return '&'.join(args)
        return locals()
    query = property(**query())

    def request():
        def fget(self):
            r = self.path
            if self.query:
                r = r + '?%s' % self.query
            if self.fragment:
                r = r + '#%s' % self.fragment
            return r
        return locals()
    request = property(**request())

    def __str__(self):
        return '%s://%s%s' % (self.scheme, self.hostname, self.request)


# shorthands
urlopener = UrlOpener()
get_url = urlopener.get_url
