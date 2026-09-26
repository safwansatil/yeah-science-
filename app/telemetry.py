"""Latest values received from the rover. The UI also uses these for its map."""
import time


class TelemetryStore:
    def __init__(self):
        self.reset()

    def reset(self):
        self.values = {"x": 0.0, "y": 0.0, "heading": 0.0, "left": 0.0,
                       "right": 0.0, "battery": 0.0, "failsafe": True}
        self.received_at = None
        self.sequence = None

    def update(self, packet, now=None):
        self.values = {key: packet[key] for key in self.values}
        self.received_at = time.monotonic() if now is None else now
        self.sequence = packet["seq"]

    def is_stale(self, stale_after_ms, now=None):
        if self.received_at is None:
            return False
        current = time.monotonic() if now is None else now
        return (current - self.received_at) * 1000.0 > stale_after_ms
