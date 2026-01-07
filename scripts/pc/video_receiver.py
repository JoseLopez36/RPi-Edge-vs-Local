import gi
import threading
import logging

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('video_receiver')

class VideoReceiver:
    def __init__(self, callback):
        # Initialize GStreamer
        Gst.init_check(None)
        
        self.pipeline = None
        self.callback = callback # Function to call with decoded frames
        
        # Create a separate MainContext for the GStreamer loop
        self.context = GLib.MainContext()
        self.loop = GLib.MainLoop(self.context)
        self.loop_thread = None
        
    def start_receiving(self, port, force_software_decoder=False):
        """Starts listening for video stream on the specified port using GStreamer"""
        log.info(f"Starting video receiver on port {port}")
        
        # Pipeline description:
        # Part 1: UDP Source
        # udpsrc: receives packets from the network using UDP
        # application/x-rtp...: capsfilter to specify RTP H.264 format
        # rtph264depay: extracts H.264 stream from RTP packets
        UDP_SOURCE = [
            f"udpsrc port={port}", "!",
            "application/x-rtp,encoding-name=H264,payload=96", "!",
            "rtph264depay", "!",
        ]
        
        # Part 2: Decoding and Sink
        # h264parse: parses the H.264 stream
        # decoder: hardware or software decoder
        # videoconvert: ensures format compatibility with OpenCV
        # appsink: sends buffers to the application
        
        # Select best available decoder
        decoder = "avdec_h264" # Fallback
        if not force_software_decoder:
            if Gst.ElementFactory.find("nvh264dec"):
                log.info("Using NVIDIA hardware decoder: nvh264dec")
                decoder = "nvh264dec"
            elif Gst.ElementFactory.find("vaapih264dec"):
                log.info("Using VA-API hardware decoder: vaapih264dec")
                decoder = "vaapih264dec"
            else:
                log.info("Using software decoder: avdec_h264")
        else:
            log.info("Forcing software decoder: avdec_h264")

        DECODE_PIPELINE = [
            "h264parse", "!",
            decoder, "!",
            "videoconvert", "!",
            "video/x-raw,format=BGR", "!",
            "appsink name=sink emit-signals=True sync=False"
        ]

        # Combine parts
        full_pipeline = UDP_SOURCE + DECODE_PIPELINE
        pipeline_str = " ".join(full_pipeline)
        
        try:
            # Launch the pipeline
            self.pipeline = Gst.parse_launch(pipeline_str)
            
            # Get the sink element to connect signal
            sink = self.pipeline.get_by_name("sink")
            if not sink:
                log.error("Error: Could not find appsink in pipeline")
                return

            sink.connect("new-sample", self._on_new_sample)
    
            
            # Start the pipeline
            ret = self.pipeline.set_state(Gst.State.PLAYING)
            if ret == Gst.StateChangeReturn.FAILURE:
                log.error("Error: Unable to set the pipeline to the playing state.")
                return
            
            # Start MainLoop in a separate thread
            self.loop_thread = threading.Thread(target=self._run_loop)
            self.loop_thread.daemon = True
            self.loop_thread.start()
            
        except Exception as e:
            log.error(f"Error creating pipeline: {e}")

    def _run_loop(self):
        """Runs the GLib MainLoop with the custom context"""
        self.context.push_thread_default()
        try:
            self.loop.run()
        finally:
            self.context.pop_thread_default()

    def stop_receiving(self):
        log.info("Stopping video receiver")
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline = None
            
        if self.loop.is_running():
            self.loop.quit()

    def _on_new_sample(self, sink):
        """Callback for appsink when a new frame is available"""
        sample = sink.emit("pull-sample")
        if not sample:
            return Gst.FlowReturn.ERROR

        buffer = sample.get_buffer()
        caps = sample.get_caps()
        
        # Extract width and height from caps
        structure = caps.get_structure(0)
        width = structure.get_value("width")
        height = structure.get_value("height")
        
        # Map buffer to get data
        success, map_info = buffer.map(Gst.MapFlags.READ)
        if not success:
            return Gst.FlowReturn.ERROR
            
        try:
            # Create numpy array from data
            # BGR format (3 channels)
            frame = np.ndarray(
                shape=(height, width, 3),
                dtype=np.uint8,
                buffer=map_info.data
            )
            
            # Call the user callback with the frame
            if self.callback:
                self.callback(frame)
                
        except Exception as e:
            log.error(f"Error processing frame: {e}")
        finally:
            buffer.unmap(map_info)
            
        return Gst.FlowReturn.OK

