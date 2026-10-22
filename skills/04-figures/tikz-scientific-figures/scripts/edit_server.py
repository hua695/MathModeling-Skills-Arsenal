#!/usr/bin/env python3
"""edit_server.py — serve bundled Method Draw, autoload one SVG, save it back.

usage: python3 edit_server.py /abs/path/to/figure.svg
Binds 127.0.0.1 on an ephemeral port, opens the browser, runs until Ctrl+C.
"""
import http.server
import os
import sys
import tempfile
import threading
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
WEBROOT = os.path.join(SKILL, "assets", "method-draw")
INJECT = b'<script src="/bootstrap.js"></script>\n</body>'


def _make_handler(target):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=WEBROOT, **k)

        def log_message(self, *a):  # keep the console quiet
            pass

        def _send(self, code, body, ctype):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/figure.svg":
                with open(target, "rb") as f:
                    self._send(200, f.read(), "image/svg+xml")
                return
            if self.path in ("/", "/index.html"):
                with open(os.path.join(WEBROOT, "index.html"), "rb") as f:
                    html = f.read()
                html = html.replace(b"</body>", INJECT, 1)
                self._send(200, html, "text/html; charset=utf-8")
                return
            super().do_GET()

        def do_POST(self):
            if self.path != "/save":
                self._send(404, b"not found", "text/plain")
                return
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                self._send(400, b"bad length", "text/plain")
                return
            data = self.rfile.read(length)
            if not data or b"<svg" not in data:
                self._send(400, b"refused: empty or non-SVG body", "text/plain")
                return
            folder = os.path.dirname(target)
            fd, tmp = tempfile.mkstemp(dir=folder, suffix=".svg.tmp")
            try:
                with os.fdopen(fd, "wb") as f:
                    f.write(data)
                os.replace(tmp, target)   # atomic within the same dir
            except Exception:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
                self._send(500, b"save failed", "text/plain")
                return
            self._send(200, b"ok", "text/plain")

    return Handler


def build_server(target):
    """Return an HTTPServer bound to 127.0.0.1 on an ephemeral port."""
    return http.server.HTTPServer(("127.0.0.1", 0), _make_handler(target))


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: edit_server.py figure.svg")
    target = os.path.abspath(sys.argv[1])
    if not os.path.isfile(target):
        sys.exit("no such SVG: " + target)
    httpd = build_server(target)
    url = "http://127.0.0.1:%d/" % httpd.server_address[1]
    print("Editing %s" % target)
    print("Method Draw at %s  (Ctrl+C to stop)" % url)
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
