"""
Raspberry Pi TCP Video Streamer

Picamera2 streamer that sends H.264 over TCP to a connected client.
Based on https://github.com/raspberrypi/picamera2/blob/main/examples/capture_stream.py
"""

import time
import socket
import threading

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput

class Streamer:
    def __init__(
        self,
        host="0.0.0.0",
        port=10001,
        width=1280,
        height=720,
        bitrate=1000000,
    ):
        self.host = host
        self.port = port
        self.width = width
        self.height = height
        self.bitrate = bitrate

        self.picam2 = None
        self.encoder = None
        self.sock = None
        self.stream = None
        self.conn = None
        self._thread = None
        self._running = False
        self._lock = threading.Lock()

    def _run(self):
        """Internal method that runs in a separate thread."""
        try:
            self.picam2 = Picamera2()
            video_config = self.picam2.create_video_configuration(
                {"size": (self.width, self.height)}
            )
            self.picam2.configure(video_config)
            self.encoder = H264Encoder(self.bitrate)

            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((self.host, self.port))
            self.sock.listen()
            self.picam2.encoders = self.encoder
            
            print(f"Streamer listening on {self.host}:{self.port}")
            self.conn, _ = self.sock.accept()
            print("Client connected")
            
            self.stream = self.conn.makefile("wb")
            self.encoder.output = FileOutput(self.stream)

            self.picam2.start_encoder(self.encoder)
            self.picam2.start()
            
            # Keep streaming until stopped
            while self._running:
                time.sleep(0.1)
        except Exception as e:
            print(f"Streamer error: {e}")
        finally:
            self._cleanup()

    def _cleanup(self):
        """Clean up resources."""
        if self.picam2 is not None:
            try:
                self.picam2.stop()
                self.picam2.stop_encoder()
            except Exception:
                pass
            finally:
                try:
                    self.picam2.close()
                except Exception:
                    pass
                self.picam2 = None

        if self.stream is not None:
            try:
                self.stream.close()
            except Exception:
                pass
            finally:
                self.stream = None

        if self.conn is not None:
            try:
                self.conn.close()
            except Exception:
                pass
            finally:
                self.conn = None

        if self.sock is not None:
            try:
                self.sock.close()
            except Exception:
                pass
            finally:
                self.sock = None

    def start(self):
        """Start the streamer in a separate thread."""
        with self._lock:
            if self._running:
                return
            
            self._running = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self):
        """Stop the streamer and wait for the thread to finish."""
        with self._lock:
            if not self._running:
                return
            
            self._running = False
            
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None
        
        self._cleanup()

    def get_url(self):
        return f"tcp://{self.host}:{self.port}"