"""Latest values received from the rover. The UI also uses these for its map."""
import time


class ConnectionState:
    DISCONNECTED = "DISCONNECTED"
    WAITING      = "WAITING"
    LIVE         = "LIVE"
    STALE        = "STALE"


class TelemetryStore:
    def __init__(self, stale_after_ms=1000):
        self.values = {"x": 0.0, "y": 0.0, "heading": 0.0, "left": 0.0,
                       "right": 0.0, "battery": 0.0, "failsafe": True}
        self.received_at = None      # None means "never received"
        self.sequence = None
        self._stale_after_s = stale_after_ms / 1000.0
        self._state = ConnectionState.DISCONNECTED

    @property
    def state(self):
        return self._state

    def on_link_opened(self):
        """Called when the socket opens."""
        self._state = ConnectionState.WAITING

    def on_link_closed(self):
        """Called when the socket closes."""
        self._state = ConnectionState.DISCONNECTED
        self.received_at = None
        self.sequence = None

    def update(self, packet):
        """Called for each valid telemetry packet."""
        self.values = {key: packet[key] for key in self.values}
        self.received_at = time.monotonic()
        self.sequence = packet["seq"]
        self._state = ConnectionState.LIVE

    def tick(self):
        """Called periodically to detect staleness."""
        if self._state != ConnectionState.LIVE:
            return False
        if self.received_at is None:
            return False
        if time.monotonic() - self.received_at > self._stale_after_s:
            self._state = ConnectionState.STALE
            return True
        return False
        