"""
Raspberry Pi Video Streamer

This module uses picamera to stream the video from the Raspberry Pi Camera
Based on the example code from the official PiCamera package
http://picamera.readthedocs.io/en/latest/recipes2.html#web-streaming
"""

import io
import picamera
import logging
import socketserver
from threading import Condition
from http import server

class StreamOutput(object):
    """Output handler for PiCamera that buffers frames for streaming"""
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

class StreamHandler(server.BaseHTTPRequestHandler):
    """HTTP request handler for streaming video"""
    def __init__(self, *args, output=None, **kwargs):
        self.output = output
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            # Generate HTML page with dynamic resolution
            width = getattr(self.server, 'stream_width', 640)
            height = getattr(self.server, 'stream_height', 480)
            page = f"""\
            <html>
            <head>
            <title>RPi Virtual PTZ - Video Stream</title>
            </head>
            <body>
            <center><h1>RPi Virtual PTZ - Video Stream</h1></center>
            <center><img src="stream.mjpg" width="{width}" height="{height}"></center>
            </body>
            </html>
            """
            content = page.encode('utf-8')
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
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with self.output.condition:
                        self.output.condition.wait()
                        frame = self.output.frame
                    self.wfile.write(b'--FRAME\r\n')
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

class StreamServer(socketserver.ThreadingMixIn, server.HTTPServer):
    """Threading HTTP server for video streaming"""
    allow_reuse_address = True
    daemon_threads = True

class Streamer(object):
    """Main streamer class that manages camera and HTTP streaming server"""
    def __init__(self, width=1920, height=1080, framerate=30, port=8000):
        self.width = width
        self.height = height
        self.framerate = framerate
        self.port = port
        
        self.camera = None
        self.output = None
        self.server = None

    def start(self):
        """Start the camera and streaming server"""
        if self.camera is not None:
            logging.warning("Streamer already started")
            return
        
        resolution = f"{self.width}x{self.height}"
        self.camera = picamera.PiCamera(resolution=resolution, framerate=self.framerate)
        
        self.output = StreamOutput()
        self.camera.start_recording(self.output, format='mjpeg')
        
        # Create handler factory that passes output reference
        def handler_factory(*args, **kwargs):
            return StreamHandler(*args, output=self.output, **kwargs)
        
        address = ('', self.port)
        self.server = StreamServer(address, handler_factory)
        self.server.stream_width = self.width
        self.server.stream_height = self.height
        
        # Start server in a separate thread
        import threading
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        
        logging.info(f"Stream started: {resolution} @ {self.framerate}fps on port {self.port}")

    def stop(self):
        """Stop the camera and streaming server"""
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        
        if self.camera is not None:
            self.camera.stop_recording()
            self.camera.close()
            self.camera = None
        
        self.output = None
        logging.info("Stream stopped")

    def get_local_url(self):
        return f"http://127.0.0.1:{self.port}"

    def get_local_stream_url(self):
        return f"{self.get_local_url()}/stream.mjpg"