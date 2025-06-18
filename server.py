from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import json
from typing import Callable, Dict

_routes: Dict[str, Callable[[str], dict]] = {}

def route(path: str, method: str):
    def decorator(func: Callable[[str], dict]):
        _routes[f"{method.upper()} {path}"] = func
        return func
    return decorator

class RequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.end_headers()

    def do_GET(self):
        self._dispatch()

    def do_POST(self):
        self._dispatch()

    def _dispatch(self):
        handler = _routes.get(f"{self.command} {self.path}")
        if not handler:
            self._set_headers(404)
            self.wfile.write(b'{"error":"Not Found"}')
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b""

        try:
            resp = handler(body.decode())
            self._set_headers(200)
            self.wfile.write(json.dumps(resp).encode())
        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode())

@route("/server_on", method="GET")
def echo(body: str):
    return {"server_on": True}
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

def run(host: str = "localhost", port: int = 8000):
    server = ThreadedHTTPServer((host, port), RequestHandler)
    print(f"Server started on http://{host}:{port}  (Ctrl-C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server shutting down")
        server.server_close()

if __name__ == "__main__":
    run("localhost", 8000)
