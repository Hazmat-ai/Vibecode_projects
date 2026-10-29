"""Local-only static preview with a small public-file allowlist; no app API."""
import argparse
import http.server
import pathlib
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        path = urllib.parse.unquote(urllib.parse.urlsplit(self.path).path)
        if path == "/":
            self.path = "/simulator.html"
        elif path != "/simulator.html" and not path.startswith("/simulator/"):
            self.send_error(404)
            return
        target = pathlib.Path(self.translate_path(self.path)).resolve()
        if not target.is_file() or ROOT not in target.parents or (path != "/" and path != "/simulator.html" and ROOT / "simulator" not in target.parents):
            self.send_error(404)
            return
        super().do_GET()

    def do_HEAD(self):
        self.send_error(405)

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'; base-uri 'self'")
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=3000)
    args = parser.parse_args()
    http.server.ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
