import base64
import cv2
import datetime
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
        '.css':'text/css', '.avi': 'video/x-msvideo'}

cap = cv2.VideoCapture(0)
fourcc = cv2.VideoWriter_fourcc(*'XVID')
capture = False
out = None
lasttime = None

def __main__():
    thread = threading.Thread(target=httpServe)
    thread.start()
    
    try:
        while cap.isOpened():
            time.sleep(1)
    except KeyboardInterrupt:
        cap.release()
        return

def httpServe():
    handler = StubHttpRequestHandler
    httpd = HTTPServer(('',PORT),handler)
    httpd.serve_forever()

def videoCapture():
    global capture
    global out

    while capture:
        nowtime = time.time()
        if nowtime - lasttime > 10:
            capture = False
            out.release()
            out = None
            break
        _, img = cap.read()
        out.write(img)

class StubHttpRequestHandler(BaseHTTPRequestHandler):
    server_version = "HTTP Stub/0.1"
    thread = None
    aviFilename = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/Streaming':
            global lasttime
            lasttime = time.time()

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

    def do_POST(self):
        global thread
        global aviFilename
        global capture
        global out

        content_len = int(self.headers.get('content-length'))
        requestBody = json.loads(self.rfile.read(content_len).decode('utf-8'))

        if requestBody['contents']['command'] == 1:
            _, img = cap.read()
            dt_now = datetime.datetime.now()
            filename = dt_now.strftime('%Y%m%d_%H%M%S')+".jpg"
            cv2.imwrite(filename, img)

            response = {
                'status' : 200,
                'path': "http://pi4.local:8000/" + filename
            }
        if requestBody['contents']['command'] == 2:
            dt_now = datetime.datetime.now()
            aviFilename = dt_now.strftime('%Y%m%d_%H%M%S')+".avi"
            out = cv2.VideoWriter(aviFilename, fourcc, 20.0, (640,480))
            
            capture = True
            thread = threading.Thread(target=videoCapture)
            thread.start()

            response = {
                'status' : 200,
            }
        if requestBody['contents']['command'] == 3:
            capture = False

            thread.join()

            out.release()
            out = None

            response = {
                'status' : 200,
                'path': "http://pi4.local:8000/" + aviFilename
            }
        else:
            response = {
                'status' : 200
            }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        responseBody = json.dumps(response)

        self.wfile.write(responseBody.encode('utf-8'))

__main__()
