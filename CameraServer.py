import base64
import cv2
import json
import os
import pathlib
import sys
import time
import threading

from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from http import HTTPStatus
from urllib.parse import urlparse

PORT = 8000
CONTENT_TYPE = {'.html': 'text/html; charset=utf-8', '.txt': 'text/plain; charset=utf-8', '.js': 'text/javascript', '.json': 'application/json',
        '.jpeg': 'image/jpeg', '.jpg': 'image/jpeg', '.png': 'image/png', '.gif': 'image/gif',
        '.css':'text/css'}

cap = cv2.VideoCapture(0)

def __main__():
    thread = threading.Thread(target=httpServe)
    thread.start()
    
    try:
        while cap.isOpened():
            time.sleep(1)
    except KeyboardInterrupt:
        return

def httpServe():
    handler = StubHttpRequestHandler
    httpd = HTTPServer(('',PORT),handler)
    httpd.serve_forever()

class StubHttpRequestHandler(BaseHTTPRequestHandler):
    server_version = "HTTP Stub/0.1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/Streaming':
            enc = sys.getfilesystemencoding()

            _, img = cap.read()
            resized_img = cv2.resize(img, (480, 320))
            _, encoded_img = cv2.imencode('.jpg', resized_img, [int(cv2.IMWRITE_JPEG_QUALITY), 30])
            dst_base64 = base64.b64encode(encoded_img).decode('utf-8')

            data = {
                'image': 'data:image/jpg;base64,' + dst_base64
            }

            encoded = json.dumps(data).encode()

            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", "text/html; charset=%s" % enc)
            self.send_header("Access-Control-Allow-Origin", "null")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()

            self.wfile.write(encoded)
        elif parsed.path.endswith('/'):
            self.send_response(HTTPStatus.OK)
            with open('index.html',mode='br') as f:
                data = f.read()
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(bytes(data))
        else:
            self.send_response(HTTPStatus.OK)
            filepath = '.' + parsed.path
            with open(filepath, mode='br') as f:
                data = f.read()
            self.send_header("Content-type", CONTENT_TYPE[pathlib.Path(filepath).suffix])
            self.end_headers()
            self.wfile.write(bytes(data))

__main__()
