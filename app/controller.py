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
        self.telemetry = TelemetryStore(stale_after_ms=config.get("stale_after_ms", 1000))
        self._online = False
        self._armed = False
        self._left = self._right = 0.0
        self._speed = config["drive_speed"]
        self._seq = 0
        self._held_keys = set()
        self._mouse_active = False
        self._events = []
        self._invalid = 0
        self._timer = QTimer(self)
        self._timer.setInterval(config["send_period_ms"])
        self._timer.timeout.connect(self.tick)
        self._timer.start()
        self.note("Station ready. Start the simulator, then connect.")

    connected = Property(bool, lambda self: self._online, notify=changed)
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
    connectionState = Property(str, lambda self: self.telemetry.state, notify=changed)

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
            self.telemetry.on_link_opened()
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
        self.stop()
        self._armed = False
        self.link.close()
        self._online = False
        self.telemetry.on_link_closed()
        self.note("Datalink closed")
        self.changed.emit()

    @Slot()
    def toggleArm(self):
        if not self._online:
            self.note("Connect before enabling drive", True)
            return
        self.stop()
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
        if self.telemetry.state != "LIVE":
            return
        if not (math.isfinite(left) and math.isfinite(right)):
            return
        self._left = max(-1.0, min(1.0, left)) * self._speed
        self._right = max(-1.0, min(1.0, right)) * self._speed
        self._send_drive()
        self.changed.emit()

    _KEY_MAP = {
    "W": "forward", "Up": "forward",
    "S": "backward", "Down": "backward",
    "A": "left", "Left": "left",
    "D": "right", "Right": "right",
    }

    @Slot()
    def mouseDown(self):
        self._mouse_active = True

    @Slot()
    def stopMouse(self):
        self._mouse_active = False
        if self._held_keys:
            self._recompute_drive()
        else:
            self.stop()

    @staticmethod
    def _key_to_direction(key):
        return Station._KEY_MAP.get(key)

    @Slot(str)
    def keyDown(self, key):
        direction = Station._key_to_direction(key)
        if direction is None:
            return
        if direction not in self._held_keys:
            self._held_keys.add(direction)
            if not self._mouse_active and self.telemetry.state == "LIVE":
                self._recompute_drive()

    @Slot(str)
    def keyUp(self, key):
        direction = Station._key_to_direction(key)
        if direction is None:
            return
        if direction in self._held_keys:
            self._held_keys.discard(direction)
            if not self._mouse_active:
                self._recompute_drive()

    def _recompute_drive(self):
        fwd = (1 if "forward" in self._held_keys else 0) - (1 if "backward" in self._held_keys else 0)
        rot = (1 if "left" in self._held_keys else 0) - (1 if "right" in self._held_keys else 0)

        left  = max(-1.0, min(1.0, fwd - rot))
        right = max(-1.0, min(1.0, fwd + rot))

        if left == 0.0 and right == 0.0:
            self.stop()
        else:
            self.setDrive(left, right)

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
            self._mouse_active = False
            self._left = self._right = 0.0
            self._send_drive()
            self.changed.emit()

    @Slot()
    def tick(self):
        if self._online:
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
                    self.telemetry.update(packet)
                    if first:
                        self.note("First rover telemetry received")
            if self._armed:
                self._send_drive()
        if self.telemetry.tick():
            print(">>> TRANSITION to STALE at", time.monotonic())
            self.note("Telemetry stale — no valid packet within threshold", True)
            self.stop()
        print("STATE:", self.telemetry.state, "| received_at:", self.telemetry.received_at)
        self.changed.emit()

    @Slot()
    def clearEvents(self):
        self._events = []
        self.eventsChanged.emit()

    @Slot()
    def shutdown(self):
        self._timer.stop()
        self.disconnectLink()
