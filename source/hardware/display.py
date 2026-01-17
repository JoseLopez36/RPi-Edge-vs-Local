"""
Sense HAT visual radar display.
"""

try:
    from sense_hat import SenseHat
except Exception:  # pragma: no cover - optional hardware dependency
    SenseHat = None


class VisualRadar:
    def __init__(self, enabled=True):
        self.enabled = bool(enabled) and SenseHat is not None
        self.hat = SenseHat() if self.enabled else None

    def _map_to_matrix(self, x, y, frame_w, frame_h):
        if frame_w <= 0 or frame_h <= 0:
            return 0, 0
        col = int((x / frame_w) * 7)
        row = int((y / frame_h) * 7)
        col = max(0, min(7, col))
        row = max(0, min(7, row))
        return col, row

    def update(self, targets, active_id, frame_w, frame_h):
        if not self.enabled or self.hat is None:
            return

        pixels = [(0, 0, 0)] * 64
        for idx, target in enumerate(targets or []):
            bbox = target.get("bbox")
            if not bbox or len(bbox) < 4:
                continue
            cx = (bbox[0] + bbox[2]) / 2
            cy = (bbox[1] + bbox[3]) / 2
            col, row = self._map_to_matrix(cx, cy, frame_w, frame_h)
            key = target.get("id")
            if key is None:
                key = idx
            color = (255, 0, 0) if key == active_id else (255, 255, 255)
            pixels[row * 8 + col] = color

        self.hat.set_pixels(pixels)

    def clear(self):
        if self.enabled and self.hat is not None:
            self.hat.clear()

    def close(self):
        self.clear()