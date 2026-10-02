"""Latest values received from the rover. The UI also uses these for its map."""
import time


class TelemetryStore:
    def __init__(self):
        self.values = {"x": 0.0, "y": 0.0, "heading": 0.0, "left": 0.0,
                       "right": 0.0, "battery": 0.0, "failsafe": True}
        self.received_at = None
        self.sequence = None

    def update(self, packet):
        self.values = {key: packet[key] for key in self.values}
        self.received_at = time.monotonic()
        self.sequence = packet["seq"]

    def status(self, stale_after_ms, connection):
        if connection is False:
            return "Disconnected"
        if self.received_at is None:
            return "Waiting"
        if (time.monotonic() - self.received_at) * 1000 >= stale_after_ms:
            return "Stale"
        return "Live"

