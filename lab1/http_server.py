import http.server
import socketserver
import json
from urllib.parse import urlparse, parse_qs

PORT = 8080

class MyHandler(http.server.SimpleHTTPRequestHandler):
    notes = {}

    def do_GET(self):
        url = urlparse(self.path) # get only the url
        params = parse_qs(url.query) # get the params in format {key:[values]}

        if url.path == "/":
            self._send(200, "text/plain", b"OK\n")

        elif url.path == "/echo" and "msg" in params:
            text = params["msg"][0]
            # tranform a py dict to json bytes
            body = json.dumps({"msg": text}).encode()
            self._send(200, "application/json", body)

        elif url.path.startswith("/notes/"):

            note_id = url.path.split('/')[-1]
            
            if not note_id.isdigit():
                self._send(404, "application/json", b'{"error": "invalid ID"}')
                return
            else:
                note_id = int(note_id)

            if note_id not in self.notes:
                self._send(404, "application/json", b'{"error": "note not found"}')
                return
            
            note = self.notes.get(note_id)
            body = json.dumps(note).encode("utf-8")
            self._send(200, "application/json", body)

        else:
            self._send(404, "text/plain", b"PATH NOT FOUND\n")

    def do_POST(self):
        url = urlparse(self.path)
        ctype = self.headers.get("Content-Type")

        if url.path != "/notes":
            self._send(404, "text/plain", b"NOT FOUND\n")
            return

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        
        try:
            data = json.loads(raw)
        except:
            self._send(400, "application/json", b'{"error": "invalid JSON"}')
            return

        if not isinstance(data.get("text"), str):
            self._send(400, "application/json", b'{"error": "missing text"}')
            return

        if ctype != "application/json":
            self._send(415, "application/json", b'{"error": "invalid ctype"}')

        note_id = len(self.notes) + 1
        note = {"id": note_id, "text": data["text"]}
        self.notes[note_id] = note

        body = json.dumps(note).encode()
        self._send(201, "application/json", body)

    def do_DELETE(self):
        url = urlparse(self.path)

        if not url.path.startswith("/notes"):
            self._send(404, "text/plain", b"NOT FOUND\n")
            return

        note_id = url.path.split('/')[-1]
        
        if not note_id.isdigit():
            self._send(404, "application/json", b'{"error": "invalid ID"}')
            return
        else:
            note_id = int(note_id)
        
        if note_id not in self.notes:
            self._send(404, "application/json", b'{"error": "note not found"}')
            return

        del self.notes[note_id]          # remove the element in the dict
        self._send(204, "text/plain", b"")

    def do_PUT(self): self._method_not_allowed()

    def _send(self, code, ctype, body: bytes):
        self.send_response(code)                
        self.send_header("Content-Type", ctype)  
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()                       
        self.wfile.write(body)     # write the body of the response regarding the socket      

    def _method_not_allowed(self):
        self.send_response(405)
        self.send_header("Allow", "GET, POST, DELETE")          
        self.send_header("Content-Type", "application/json")
        self.end_headers()

with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print(f"Serving at port {PORT}")
    httpd.serve_forever()