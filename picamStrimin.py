import io
import os
import picamera
import logging
import socketserver
from threading import Condition
from http import server
from piPins import *
import json

post_count = 0
car = CarController()

# https://picamera.readthedocs.io/en/release-1.13/recipes2.html#web-streaming

# As per https://www.raspberrypi.org/forums/viewtopic.php?f=43&t=241633, the AWB algorithm was updated a month ago.
# Can you check whether this is an issue with the new algorithm by running sudo vcdbg set awb_mode 0 before running raspivid. AWB is never really expecting the IR component, therefore it could be doing odd things.

# Убрать красноту камеры sudo vcdbg set awb_mode 0
PAGE="""\
<html>
<head>
<title>picamera MJPEG streaming demo</title>
<script>
function doPost(){
var xhr = new XMLHttpRequest();
xhr.open("POST", '/server', true);
xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
xhr.onreadystatechange = function() { // Call a function when the state changes.
    if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
        // Request finished. Do processing here.
    }
}
xhr.send("foo=bar&lorem=ipsum");
}
</script>
</head>
<body>
<h1>PiCamera MJPEG Streaming Demo</h1>
<img src="stream.mjpg" width="640" height="480" />
<br/>
<a href="forward.html">Forward</a>
<a href="#" onclick="doPost()">test post</a>
</body>
</html>
"""

class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_POST(self):
        global post_count
        post_count += 1
        logging.info("post_count=" + str(post_count))
        #logging.info(self.parse_request())
        #logging.info(self.log_request())
        content_len = int(self.headers.get('Content-Length'))
        post_body = self.rfile.read(content_len)
        #logging.info(type(post_body))
        s = post_body.decode("utf-8")
        logging.info("post_body " + s)
        s = json.loads(s)
        angle, strength = s["angle"], s["strength"]
        car.ride(angle, strength)
        content = '{"result":"ok"}'.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; utf-8')
        self.send_header('Content-Length', len(content))
        self.end_headers()
        self.wfile.write(content)
        
    def do_GET(self):
        #self.car = CarController() # todo WITH CarController()
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/forward.html':
            logging.info("forward")
            self.send_response(301)
            self.send_header('Location', '/index.html')
            
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            #self.car.go_forward()
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=MyBoundaryFRAME')
            
            #self.send_header('Keep-Alive', 'timeout=5, max=100')
            #self.send_header('Connection', 'Keep-Alive')
            #self.send_header('Transfer-Encoding', 'chunked')
                        
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--MyBoundaryFRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


format = "%(asctime)s: %(message)s"
logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
logging.info('pid %s', os.getpid())
with picamera.PiCamera(resolution='640x480', framerate=5) as camera:
    #init_pins()
    output = StreamingOutput()
    #camera.start_preview()
    #camera.awb_mode = 'off'
    camera.start_recording(output, format='mjpeg')

    #camera.led = Falseq
    try:
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        logging.info('stopping')
        camera.stop_recording() 
        #GPIO.cleanup()
        logging.info('stopped')
        #upon exiting the with statement, the camera.close() method is automatically called