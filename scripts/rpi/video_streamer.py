"""
Video Streamer Module

This module streams annotated video to a PC using GStreamer.
"""

import gi
import threading
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

class VideoStreamer:
    """Video streamer with YOLO tracking, annotation, and gimbal control"""
    
    def __init__(self, video_input, tracker, gimbal):
        """
        Initialize video streamer
        
        Args:
            video_input: SiyiVideoInput instance
            tracker: YOLOTracker instance
            gimbal: SiyiGimbalController instance
        """
        self.video_input = video_input
        self.tracker = tracker
        self.gimbal = gimbal
        
        Gst.init(None)
        self.pipeline = None
        self.loop = GLib.MainLoop()
        self.loop_thread = None
        
        # Frame processing
        self.frame_queue = []
        self.frame_lock = threading.Lock()
        self.running = False
        
        print("Video Streamer initialized")