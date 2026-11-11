"""Bridge loopback -> Unix socket; chạy duy nhất CLI được runner chỉ định."""
import http.client
import http.server
import json
import os
import pathlib
import socket
import subprocess
import sys
import threading
from proxy_headers import REQUEST_HEADERS, RESPONSE_HEADERS, protocol_headers


class UnixHTTP(http.client.HTTPConnection):
    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        # Includes up to 30s intentional pacing plus the 45s upstream socket timeout.
        self.sock.settimeout(90)
        self.sock.connect(sys.argv[1])


class Bridge(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_message(self, *args):
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        if not 0 < length <= 2 * 1024 * 1024:
            self.send_error(413)
            return
        connection = UnixHTTP("broker")
        try:
            headers = protocol_headers(self.headers, REQUEST_HEADERS)
            headers.update({"Content-Type": "application/json", "Authorization": self.headers.get("Authorization", "")})
            connection.request("POST", self.path, self.rfile.read(length),
                               headers)
            response = connection.getresponse()
            self.send_response(response.status)
            self.send_header("Content-Type", response.getheader("Content-Type", "application/json"))
            for name, value in protocol_headers(response.headers, RESPONSE_HEADERS).items():
                self.send_header(name, value)
            self.end_headers()
            while data := response.readline(1024 * 1024):
                self.wfile.write(data)
                self.wfile.flush()
        except (OSError, http.client.HTTPException):
            self.close_connection = True
        finally:
            connection.close()


def main():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 8765), Bridge)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    root = pathlib.Path.cwd().parent
    witness = {"net_namespace": os.readlink("/proc/self/ns/net"), "cwd": str(pathlib.Path.cwd()),
               "real_home_hidden": not pathlib.Path("/home/tts").exists(),
               "provider_key_absent": not any(name in os.environ for name in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"])}
    (root / "witness.json").write_text(json.dumps(witness, indent=2))
    try:
        code = subprocess.call(json.loads(sys.argv[2]), stdin=subprocess.DEVNULL)
    finally:
        server.shutdown()
        server.server_close()
    sys.exit(code)


if __name__ == "__main__":
    main()
