import time
import socket
import threading

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput

class CameraStream:
    def __init__(self, config):
        self.host = config['video']['host']
        self.port = config['video']['port']
        self.resolution = tuple(config['video']['resolution'])

        self.running = False
        self.thread = None
        self.server_socket = None
        self.client_socket = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.stream_loop)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def stream_loop(self):
        print(f"Starting video stream on {self.host}:{self.port}")
        
        picam2 = Picamera2()
        try:
            video_config = picam2.create_video_configuration({"size": self.resolution})
            picam2.configure(video_config)
            encoder = H264Encoder(1000000)

            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen()
            
            print("Waiting for connection...")
            self.server_socket.settimeout(1.0)
            
            while self.running:
                try:
                    self.client_socket, addr = self.server_socket.accept()
                    print(f"Connection from {addr}")
                    break
                except socket.timeout:
                    continue
            
            if not self.running:
                return

            picam2.encoders = encoder
            stream = self.client_socket.makefile("wb")
            encoder.output = FileOutput(stream)
            
            picam2.start_encoder(encoder)
            picam2.start()
            
            while self.running:
                time.sleep(0.1)
                
            picam2.stop()
            picam2.stop_encoder()
            
        except Exception as e:
            print(f"Streaming error: {e}")
        finally:
            if self.client_socket:
                self.client_socket.close()
            if self.server_socket:
                self.server_socket.close()