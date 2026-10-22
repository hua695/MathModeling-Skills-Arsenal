# scripts/tests/test_edit_server.py
import os, sys, shutil, tempfile, threading, unittest, urllib.request, urllib.error
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import edit_server  # noqa: E402

SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>'

class ServerCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.svg = os.path.join(self.dir, "figure.svg")
        with open(self.svg, "w") as f:
            f.write(SVG)
        self.httpd = edit_server.build_server(self.svg)
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        shutil.rmtree(self.dir, ignore_errors=True)

    def url(self, p):
        return "http://127.0.0.1:%d%s" % (self.port, p)

    def test_get_figure_svg_returns_file(self):
        body = urllib.request.urlopen(self.url("/figure.svg")).read().decode()
        self.assertEqual(body, SVG)

    def test_post_save_writes_back(self):
        new = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"></svg>'
        req = urllib.request.Request(
            self.url("/save"), data=new.encode(),
            headers={"Content-Type": "image/svg+xml"}, method="POST")
        resp = urllib.request.urlopen(req)
        self.assertEqual(resp.status, 200)
        with open(self.svg) as f:
            self.assertEqual(f.read(), new)

    def test_index_injects_bootstrap(self):
        html = urllib.request.urlopen(self.url("/")).read().decode()
        self.assertIn('<script src="/bootstrap.js"></script>', html)
        self.assertEqual(html.count("<script src=\"/bootstrap.js\"></script>"), 1)

    def test_post_save_bad_length_400(self):
        import http.client
        conn = http.client.HTTPConnection("127.0.0.1", self.port)
        conn.putrequest("POST", "/save")
        conn.putheader("Content-Length", "notanumber")
        conn.endheaders()
        # no body sent; server should reject the malformed length
        try:
            resp = conn.getresponse()
            self.assertEqual(resp.status, 400)
        finally:
            conn.close()

    def test_post_save_empty_body_refused(self):
        before = open(self.svg).read()
        req = urllib.request.Request(
            self.url("/save"), data=b"",
            headers={"Content-Type": "image/svg+xml"}, method="POST")
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(req)
        self.assertEqual(cm.exception.code, 400)
        self.assertEqual(open(self.svg).read(), before)  # target untouched

    def test_post_unknown_path_404(self):
        req = urllib.request.Request(self.url("/nope"), data=b"x", method="POST")
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(req)
        self.assertEqual(cm.exception.code, 404)

if __name__ == "__main__":
    unittest.main()
