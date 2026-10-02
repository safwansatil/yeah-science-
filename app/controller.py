"""Station coordinator. Input, transport and display state meet here.

This class has grown with the UI; there is room to separate responsibilities
when someone next changes it. Keep the mouse controls working while doing so.
"""
import logging
import math
import time

from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot

from app.telemetry import TelemetryStore
from link.packets import decode, encode
from link.udp import UdpLink

log = logging.getLogger("station")


class Station(QObject):
    changed = Signal()
    eventsChanged = Signal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.link = UdpLink(config["station_port"], config["rover_port"])
        self.telemetry = TelemetryStore()
        self._online = False
        self._armed = False
        self._was_live = False
        self._left = self._right = 0.0
        self._speed = config["drive_speed"]
        self._seq = 0
        self._events = []
        self._invalid = 0
        self._held_keys = set()
        self._timer = QTimer(self)
        self._timer.setInterval(config["send_period_ms"])
        self._timer.timeout.connect(self.tick)
        self._timer.start()
        self.note("Station ready. Start the simulator, then connect.")

    @property
    def link_state(self):
        if not self._online:
            return "DISCONNECTED"
        if self.telemetry.received_at is None:
            return "WAITING"
        stale_timeout = self.config.get("stale_after_ms", 1000) / 1000.0
        if self.telemetry.is_stale(stale_timeout):
            return "STALE"
        return "LIVE"

    connected = Property(bool, lambda self: self._online, notify=changed)
    linkState = Property(str, lambda self: self.link_state, notify=changed)
    isLive = Property(bool, lambda self: self.link_state == "LIVE", notify=changed)
    isStale = Property(bool, lambda self: self.link_state == "STALE", notify=changed)
    stateColor = Property(str, lambda self: {
        "LIVE": "#00e676",
        "STALE": "#f3c623",
        "WAITING": "#38bdf8",
        "DISCONNECTED": "#7a8b9e"
    }.get(self.link_state, "#7a8b9e"), notify=changed)
    armed = Property(bool, lambda self: self._armed, notify=changed)
    telemetryData = Property("QVariantMap", lambda self: self.telemetry.values, notify=changed)
    eventLines = Property("QStringList", lambda self: self._events, notify=eventsChanged)
    speed = Property(float, lambda self: self._speed, notify=changed)
    leftCommand = Property(float, lambda self: self._left, notify=changed)
    rightCommand = Property(float, lambda self: self._right, notify=changed)
    rxBytes = Property(int, lambda self: self.link.rx, notify=changed)
    txBytes = Property(int, lambda self: self.link.tx, notify=changed)
    invalidPackets = Property(int, lambda self: self._invalid, notify=changed)
    endpoint = Property(str, lambda self: f"127.0.0.1:{self.config['rover_port']}", constant=True)

    @Property(str, notify=changed)
    def batteryText(self):
        if self.link_state in ("DISCONNECTED", "WAITING"):
            return "--"
        val = f"{self.telemetry.values['battery']:.2f}"
        return f"{val} [STALE]" if self.link_state == "STALE" else val

    @Property(str, notify=changed)
    def headingText(self):
        if self.link_state in ("DISCONNECTED", "WAITING"):
            return "--"
        val = f"{(self.telemetry.values['heading'] * 180 / math.pi):.0f}"
        return f"{val} [STALE]" if self.link_state == "STALE" else val

    @Property(str, notify=changed)
    def leftSpdText(self):
        if self.link_state in ("DISCONNECTED", "WAITING"):
            return "--"
        val = f"{self.telemetry.values['left']:.2f}"
        return f"{val} [STALE]" if self.link_state == "STALE" else val

    @Property(str, notify=changed)
    def rightSpdText(self):
        if self.link_state in ("DISCONNECTED", "WAITING"):
            return "--"
        val = f"{self.telemetry.values['right']:.2f}"
        return f"{val} [STALE]" if self.link_state == "STALE" else val

    def note(self, message, warning=False):
        (log.warning if warning else log.info)(message)
        self._events = (self._events + [time.strftime("%H:%M:%S") + "  " + message])[-80:]
        self.eventsChanged.emit()

    @Slot()
    def connectLink(self):
        if self._online:
            return
        try:
            self.link.open()
            self._online = True
            self.link.send(encode("hello", self._seq))
            self._seq += 1
            self.note("Datalink opened on port " + str(self.config["station_port"]))
        except OSError as exc:
            self.link.close()
            self._online = False
            self.note("Cannot open link: " + str(exc), True)
        self.changed.emit()

    @Slot()
    def disconnectLink(self):
        self.clearKeyboard()
        self._armed = False
        self.link.close()
        self._online = False
        self._was_live = False
        self.telemetry.reset()
        self.note("Datalink closed")
        self.changed.emit()

    @Slot()
    def toggleArm(self):
        if not self._online:
            self.note("Connect before enabling drive", True)
            return
        self.clearKeyboard()
        self._armed = not self._armed
        self.note("Drive enabled" if self._armed else "Drive disabled")
        self.changed.emit()

    @Slot(float)
    def setSpeed(self, value):
        if math.isfinite(value):
            self._speed = max(0.1, min(1.0, value))
            self.changed.emit()

    @Slot(float, float)
    def setDrive(self, left, right):
        if not self._armed or not self._online:
            return
        if not (math.isfinite(left) and math.isfinite(right)):
            return
        self._left = max(-1.0, min(1.0, left)) * self._speed
        self._right = max(-1.0, min(1.0, right)) * self._speed
        self._send_drive()
        self.changed.emit()

    def _send_drive(self):
        if not self._online:
            return
        try:
            self.link.send(encode("drive", self._seq, left=self._left, right=self._right))
            self._seq += 1
        except OSError as exc:
            self.note("Send failed: " + str(exc), True)
            self._left = self._right = 0.0
            self._armed = False
            self.link.close()
            self._online = False

    @Slot()
    def stop(self):
        self._held_keys.clear()
        self._left = self._right = 0.0
        self._send_drive()
        self.changed.emit()

    @Slot(str, bool)
    def handleKey(self, key_name, is_down):
        """Handle keyboard teleoperation inputs (WASD and arrow keys)."""
        key = key_name.lower()
        if key not in {"w", "s", "a", "d", "up", "down", "left", "right"}:
            return
        
        if is_down:
            self._held_keys.add(key)
        else:
            self._held_keys.discard(key)

        # Releasing last movement key requests zero velocity immediately
        if not self._held_keys:
            self.stop()
            return

        # Direction resolution with alias support (W and Up are aliases)
        fwd = bool(self._held_keys & {"w", "up"})
        rev = bool(self._held_keys & {"s", "down"})
        lft = bool(self._held_keys & {"a", "left"})
        rgt = bool(self._held_keys & {"d", "right"})

        # Opposing directions cancel
        linear = (1.0 if fwd else 0.0) - (1.0 if rev else 0.0)
        angular = (1.0 if lft else 0.0) - (1.0 if rgt else 0.0)

        if linear == 0.0 and angular == 0.0:
            self.stop()
            return

        # Forward-plus-turn policy:
        # If moving and steering simultaneously, curve trajectory smoothly
        if linear != 0.0 and angular != 0.0:
            if angular > 0.0:   # Turn Left while driving
                left = linear * 0.4
                right = linear * 1.0
            else:               # Turn Right while driving
                left = linear * 1.0
                right = linear * 0.4
        elif linear != 0.0:
            left = linear
            right = linear
        else:
            # In-place pivot turn
            left = -angular
            right = angular

        self.setDrive(left, right)

    @Slot()
    def clearKeyboard(self):
        """Clear remembered keyboard state and stop motors."""
        self._held_keys.clear()
        self.stop()

    @Slot()
    def tick(self):
        if self._online:
            stale_timeout = self.config.get("stale_after_ms", 1000) / 1000.0
            try:
                packets = self.link.receive()
            except OSError as exc:
                self.note("Receive failed: " + str(exc), True)
                self.disconnectLink()
                return
            for raw in packets:
                try:
                    packet = decode(raw)
                except ValueError:
                    self._invalid += 1
                    if self._invalid == 1 or self._invalid % 20 == 0:
                        self.note(f"Dropped malformed packet (total {self._invalid})", True)
                    continue
                if packet["type"] == "telemetry":
                    first = self.telemetry.received_at is None
                    was_stale = self.telemetry.is_stale(stale_timeout)
                    self.telemetry.update(packet)
                    if first:
                        self.note("First rover telemetry received")
                        self._was_live = True
                    elif was_stale:
                        self.note("Rover telemetry resumed (recovered from dropout)")
                        self._was_live = True
                        # Safety: never silently resume old held movement
                        self.clearKeyboard()

            # Staleness evaluation
            if self.telemetry.received_at is not None:
                if self.telemetry.is_stale(stale_timeout):
                    if self._was_live:
                        self._was_live = False
                        self.note("Rover telemetry STALE (>1000ms silent) — halting drive", warning=True)
                        self.stop()
                else:
                    self._was_live = True

            if self._armed:
                self._send_drive()
        self.changed.emit()

    @Slot()
    def clearEvents(self):
        self._events = []
        self.eventsChanged.emit()

    @Slot()
    def shutdown(self):
        self._timer.stop()
        self.disconnectLink()
