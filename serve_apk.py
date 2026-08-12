#!/usr/bin/env python3
import http.server
import socketserver
import os
import sys

PORT = 8888
FILE_PATH = "/workspace/Calculator-Android16.apk"
FILENAME = "Calculator-Android16.apk"

class DownloadHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        sys.stdout.write(f"Request: {self.path}\n")
        sys.stdout.flush()
        if self.path == "/" or self.path == "/download" or self.path == "/Calculator-Android16.apk":
            try:
                filesize = os.path.getsize(FILE_PATH)
                self.send_response(200)
                self.send_header("Content-Type", "application/vnd.android.package-archive")
                self.send_header("Content-Disposition", f'attachment; filename="{FILENAME}"')
                self.send_header("Content-Length", str(filesize))
                self.end_headers()
                with open(FILE_PATH, "rb") as f:
                    while True:
                        chunk = f.read(65536)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                sys.stdout.write("Download complete\n")
                sys.stdout.flush()
            except Exception as e:
                sys.stdout.write(f"Error: {e}\n")
                sys.stdout.flush()
                self.send_error(500, str(e))
        else:
            self.send_error(404, "Not Found")

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("0.0.0.0", PORT), DownloadHandler) as httpd:
    sys.stdout.write(f"Serving APK download on port {PORT}\n")
    sys.stdout.flush()
    httpd.serve_forever()
