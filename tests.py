# coding: utf-8
import unittest


class TestUrl(unittest.TestCase):
    def test_url(self):
        from uscrape import Url

        url = 'https://www.google.com/?q=foo#whee'
        u = Url(url)

        self.assertEqual(u.hostname, 'www.google.com')
        self.assertEqual(u.domain, 'google.com')
        self.assertEqual(u.scheme, 'https')
        self.assertEqual(u.path, '/')

        self.assertEqual(u.request, '/?q=foo#whee')
        self.assertEqual(u.query, 'q=foo')
        self.assertEqual(u.args, {'q': 'foo'})
        self.assertEqual(u.fragment, 'whee')
        self.assertEqual(str(u), url)

        with self.assertRaises(ValueError):
            u = Url('https://www.google.com/?==')


class TestHtmlParsing(unittest.TestCase):
    def test_html_parsing(self):
        from uscrape import make_tree, to_text
        html = '''<html>
        <head>
            <title>Test Html!</title>
        </head>
        <body>
            <div id="header">
                <span>Logo(tm)</span>
                Fun header.
            </div>
            <div id="content">
                <p>Serious stuff.</p>
                <a href="relative/">Relative Link</a>
                <a href="/root/">Root</a>
                <a href="http://google.si">Another site</a>
            </div>
        </body>
        </html>
        '''

        doc = make_tree(data=html, url="http://www.google.com/foo/")

        expected = ['http://www.google.com/foo/relative/', 'http://www.google.com/root/', 'http://google.si']
        self.assertEqual(expected, [i.attrib['href'] for i in doc.xpath('//a')])

        text = doc.xpath('//div[@id="header"]/text()')
        self.assertEqual(''.join(text).strip(), 'Fun header.')

        text = to_text(doc.xpath('//div[@id="header"]')[0])
        self.assertEqual(text.strip(), 'Logo(tm) \n                Fun header.')


class TestUrlOpener(unittest.TestCase):
    def setUp(self):
        try:
            from http.server import HTTPServer, BaseHTTPRequestHandler
        except ImportError:
            from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
        import threading

        dummy_html_response = u'<html><head></head><body>Woooš!</body></html>'.encode('utf-8')
        self.dummy_html_response = dummy_html_response

        class TestReqHandler(BaseHTTPRequestHandler):
            first_500 = True

            def do_GET(self):
                if self.path in ('/raw/', '/woo/', '/woo2/'):
                    self.send_response(200)
                    # tests for charset
                    content_type = "text/html"
                    if self.path == '/woo2/':
                        content_type += '; charset=utf-8'
                    self.send_header("Content-type", content_type)
                    self.send_header("Content-length", len(dummy_html_response))
                    self.end_headers()
                    self.wfile.write(dummy_html_response)
                elif self.path == '/404/':
                    self.send_response(404)
                    self.end_headers()
                elif self.path == '/500/':
                    if TestReqHandler.first_500:
                        self.send_response(500)
                        self.end_headers()
                        TestReqHandler.first_500 = False
                    else:
                        self.send_response(404)
                        self.end_headers()

        self.server = HTTPServer(('127.0.0.1', 8080), TestReqHandler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.thread.join()

    def test_urlopener(self):
        from uscrape import urlopener
        import time

        urlopener.sleep_time = 1
        t1 = time.time()
        resp = urlopener.get_url('http://127.0.0.1:8080/woo/')
        self.assertEqual(type(resp), type([]))
        self.assertEqual(resp[0], self.dummy_html_response)

        resp = urlopener.get_url('http://127.0.0.1:8080/woo2/')
        t2 = time.time()
        self.assertGreater(t2 - t1, urlopener.sleep_time)
        self.assertEqual(resp[0], self.dummy_html_response)

        resp = urlopener.get_url('http://127.0.0.1:8080/raw/', raw=True)
        self.assertEqual(resp[0], self.dummy_html_response)

        resp = urlopener.get_url('http://127.0.0.1:8080/404/')
        self.assertEqual(resp, '')

        resp = urlopener.get_url('http://127.0.0.1:8080/500/')
        self.assertEqual(resp, '')


if __name__ == '__main__':
    unittest.main()
