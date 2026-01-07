import gi
import threading

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

class VideoStreamer:
    def __init__(self):
        try:
            Gst.init(None)
            self.pipeline = None
            self.loop = GLib.MainLoop()
            self.loop_thread = None
            print("GStreamer initialized")
        except Exception as e:
            print(f"Error initializing GStreamer: {e}")

    def start_stream(self, host, port):
        """Starts streaming H.264 video to the specified host/port via UDP using GStreamer"""
        if self.pipeline:
            print("Stream already running")
            return

        try:
            # Pipeline description:
            # libcamerasrc: Captures video from the Raspberry Pi Camera
            # video/x-raw...: Sets resolution and framerate
            # x264enc: Software H.264 encoding (tuned for low latency)
            # rtph264pay: Payloads the H.264 stream for UDP
            # udpsink: Sends the stream via UDP
            
            pipeline_str = (
                "libcamerasrc ! "
                "video/x-raw,width=1920,height=1080,framerate=30/1 ! "
                "x264enc tune=zerolatency ! "
                "rtph264pay ! "
                f"udpsink host={host} port={port}"
            )
            
            print(f"Starting pipeline: {pipeline_str}")
            self.pipeline = Gst.parse_launch(pipeline_str)
            
            # Bus handling for error messages
            bus = self.pipeline.get_bus()
            bus.add_signal_watch()
            bus.connect("message", self._on_bus_message)
            
            # Start the pipeline
            ret = self.pipeline.set_state(Gst.State.PLAYING)
            if ret == Gst.StateChangeReturn.FAILURE:
                raise RuntimeError("Unable to set the pipeline to the playing state")
            
            # Start MainLoop in a separate thread to handle GStreamer messages
            self.loop_thread = threading.Thread(target=self.loop.run)
            self.loop_thread.daemon = True
            self.loop_thread.start()
            
            print(f"Streaming to {host}:{port} started")
            
        except Exception as e:
            print(f"Failed to start stream: {e}")
            self.stop_stream()

    def stop_stream(self):
        """Stops the GStreamer pipeline"""
        if self.pipeline:
            try:
                self.pipeline.set_state(Gst.State.NULL)
                print("Pipeline stopped")
            except Exception as e:
                print(f"Error stopping pipeline: {e}")
            self.pipeline = None

        if self.loop.is_running():
            self.loop.quit()

    def _on_bus_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            print("End-of-stream")
            self.stop_stream()
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(f"GStreamer Error: {err}, {debug}")
            self.stop_stream()

