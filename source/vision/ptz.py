"""
Virtual PTZ pipeline: detect, select target, crop/zoom, stream.
"""

import time
from typing import Optional

import cv2


class PTZPipeline:
    def __init__(
        self,
        camera,
        tracker,
        streamer,
        display=None,
        joystick=None,
        sensors=None,
        config=None,
    ):
        self.camera = camera
        self.tracker = tracker
        self.streamer = streamer
        self.display = display
        self.joystick = joystick
        self.sensors = sensors
        self.config = config or {}

        ptz = self.config.get("ptz", {})
        self.zoom_min = float(ptz.get("zoom_min", 1.0))
        self.zoom_max = float(ptz.get("zoom_max", 3.0))
        self.zoom_step = float(ptz.get("zoom_step", 0.1))

        self.zoom = self.zoom_min
        self.force_wide = False
        self.active_target_id: Optional[int] = None

        self._fps = 0.0
        self._last_ts = None
        self._running = False

    def _update_fps(self):
        now = time.time()
        if self._last_ts is None:
            self._last_ts = now
            return
        dt = now - self._last_ts
        if dt <= 0:
            return
        instant = 1.0 / dt
        if self._fps <= 0:
            self._fps = instant
        else:
            self._fps = (self._fps * 0.9) + (instant * 0.1)
        self._last_ts = now

    def _apply_joystick(self, targets):
        if self.joystick is None:
            return

        updates = self.joystick.poll()
        target_delta = updates.get("target_delta", 0)
        zoom_delta = updates.get("zoom_delta", 0)
        wide = updates.get("wide", False)

        if wide:
            self.force_wide = True
            self.zoom = self.zoom_min

        if zoom_delta != 0:
            self.force_wide = False
            self.zoom = self.zoom + (zoom_delta * self.zoom_step)
            self.zoom = max(self.zoom_min, min(self.zoom_max, self.zoom))

        if target_delta != 0 and targets:
            ids = []
            for idx, t in enumerate(targets):
                tid = t.get("id")
                if tid is None:
                    tid = idx
                ids.append(tid)

            if self.active_target_id not in ids:
                self.active_target_id = ids[0]
                return

            current_idx = ids.index(self.active_target_id)
            new_idx = (current_idx + target_delta) % len(ids)
            self.active_target_id = ids[new_idx]
            self.force_wide = False

    def _select_active_target(self, targets):
        if not targets:
            return None

        for idx, target in enumerate(targets):
            tid = target.get("id")
            if tid is None:
                tid = idx
            if tid == self.active_target_id:
                return target

        return self.tracker.get_primary_target(targets)

    def _crop_and_zoom(self, frame, target):
        if frame is None:
            return None
        if target is None or self.force_wide or self.zoom <= 1.01:
            return frame

        h, w = frame.shape[:2]
        bbox = target.get("bbox")
        if not bbox or len(bbox) < 4:
            return frame

        cx = (bbox[0] + bbox[2]) / 2
        cy = (bbox[1] + bbox[3]) / 2

        crop_w = int(w / self.zoom)
        crop_h = int(h / self.zoom)
        crop_w = max(1, min(w, crop_w))
        crop_h = max(1, min(h, crop_h))

        x1 = int(cx - crop_w / 2)
        y1 = int(cy - crop_h / 2)
        x1 = max(0, min(w - crop_w, x1))
        y1 = max(0, min(h - crop_h, y1))
        x2 = x1 + crop_w
        y2 = y1 + crop_h

        cropped = frame[y1:y2, x1:x2]
        if cropped.shape[0] == 0 or cropped.shape[1] == 0:
            return frame

        return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)

    def _apply_overlay(self, frame):
        telemetry = self.config.get("telemetry", {})
        if not telemetry.get("overlay", False):
            return frame

        y = 20
        if telemetry.get("show_fps", True):
            cv2.putText(
                frame,
                f"FPS: {self._fps:.1f}",
                (10, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1,
                cv2.LINE_AA,
            )
            y += 18

        if telemetry.get("show_temp", True) and self.sensors is not None:
            temp_c = self.sensors.get_cpu_temp_c()
            if temp_c is not None:
                cv2.putText(
                    frame,
                    f"Temp: {temp_c:.1f}C",
                    (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    1,
                    cv2.LINE_AA,
                )

        return frame

    def run(self):
        self._running = True
        stream_cfg = self.config.get("stream", {})
        host = stream_cfg.get("host", "127.0.0.1")
        port = int(stream_cfg.get("port", 5000))
        fps = int(stream_cfg.get("fps", 30))

        while self._running:
            frame = self.camera.read()
            if frame is None:
                time.sleep(0.01)
                continue

            self._update_fps()

            result = self.tracker.track_frame(frame)
            targets = self.tracker.result_to_target_list(result)

            self._apply_joystick(targets)
            active_target = self._select_active_target(targets)

            if self.display is not None:
                h, w = frame.shape[:2]
                self.display.update(targets, self.active_target_id, w, h)

            output = self._crop_and_zoom(frame, active_target)
            output = self._apply_overlay(output)

            if self.streamer.pipeline is None:
                h, w = output.shape[:2]
                self.streamer.start_stream(host=host, port=port, width=w, height=h, fps=fps)

            self.streamer.push_frame(output)

    def stop(self):
        self._running = False
