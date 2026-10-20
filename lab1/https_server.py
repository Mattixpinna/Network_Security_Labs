import http.server
import ssl
from urllib.parse import urlparse
from http import cookies
import secrets
import json
from threading import Thread

def get_ssl_context(certfile, keyfile, cafile=None):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(certfile, keyfile)
    if cafile:
        context.load_verify_locations(cafile=cafile)
        context.verify_mode = ssl.CERT_REQUIRED
    return context


class MyHandler(http.server.SimpleHTTPRequestHandler):
    sessions = {}

    def do_POST(self):
        if urlparse(self.path).path != "/login":
            return self._send(404, "text/plain", b"NOT ALLOWED\n")

        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length))
            user, password = data["user"], data["password"]
        except (ValueError, KeyError, TypeError):
            return self._send(400, "application/json", b'{"error": "invalid JSON"}')

        if password != "netsec":
            return self._send(401, "text/plain", b"Wrong Password")

        sid = secrets.token_urlsafe(16)
        self.sessions[sid] = user

        C = cookies.SimpleCookie()
        C["session_id"] = sid
        C["session_id"]["path"] = "/"
        C["session_id"]["httponly"] = True
        C["session_id"]["secure"] = True
        self._send(200, "text/plain", b"OK\n", cookie=C["session_id"].OutputString())

    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == "/":
            return self._send(200, "text/plain", b"OK\n")

        if path == "/me":
            C = cookies.SimpleCookie(self.headers.get("Cookie", ""))
            sid = C["session_id"].value if "session_id" in C else None
            if sid not in self.sessions:
                return self._send(401, "text/plain", b"NO COOKIE\n")
            body = json.dumps({"user": self.sessions[sid]}).encode()
            return self._send(200, "application/json", body)

        if path == "/whoami":
            cert = self.connection.getpeercert()
            if not cert:
                return self._send(401, "text/plain", b"Not Allowed")
            # find the position of the tuple related to che Common Name
            cn = cert['subject'][0][0][1].encode()
            return self._send(200, "text/plain", cn)
        
        self._send(404, "text/plain", b"NOT FOUND\n")

    def _send(self, code, ctype, body: bytes, cookie=None):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            if cookie:
                self.send_header("Set-Cookie", cookie)
            self.end_headers()
            self.wfile.write(body)

httpd_a = http.server.ThreadingHTTPServer(("0.0.0.0", 8443), MyHandler)
httpd_b = http.server.ThreadingHTTPServer(("0.0.0.0", 8444), MyHandler)

context = get_ssl_context("server.crt", "server.key")
httpd_a.socket = context.wrap_socket(httpd_a.socket, server_side=True)

context_b = get_ssl_context("server.crt", "server.key", "ca.crt")
httpd_b.socket = context_b.wrap_socket(httpd_b.socket, server_side=True, do_handshake_on_connect=False)

threads = [Thread(target=httpd_a.serve_forever, daemon=True), Thread(target=httpd_b.serve_forever, daemon=True)]

for t in threads:
    t.start()

try:
    for t in threads:
        t.join()
except KeyboardInterrupt:
    for h in (httpd_a, httpd_b):
        h.shutdown()
        h.server_close()