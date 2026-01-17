"""
Sense HAT joystick input handler.
"""

try:
    from sense_hat import SenseHat
except Exception:  # pragma: no cover - optional hardware dependency
    SenseHat = None


class JoystickController:
    def __init__(self, enabled=True):
        self.enabled = bool(enabled) and SenseHat is not None
        self.hat = SenseHat() if self.enabled else None

    def poll(self):
        """
        Returns joystick state deltas:
        - target_delta: -1/0/1 for cycling targets
        - zoom_delta: -1/0/1 for zoom out/in
        - wide: True to reset to wide view
        """
        if not self.enabled or self.hat is None:
            return {"target_delta": 0, "zoom_delta": 0, "wide": False}

        target_delta = 0
        zoom_delta = 0
        wide = False

        for event in self.hat.stick.get_events():
            if getattr(event, "action", "") != "pressed":
                continue
            direction = getattr(event, "direction", "")
            if direction == "left":
                target_delta -= 1
            elif direction == "right":
                target_delta += 1
            elif direction == "up":
                zoom_delta += 1
            elif direction == "down":
                zoom_delta -= 1
            elif direction == "middle":
                wide = True

        return {"target_delta": target_delta, "zoom_delta": zoom_delta, "wide": wide}