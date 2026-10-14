"""Station coordinator. Input, transport and display state meet here."""

import logging
import math
import time

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

from app.telemetry import TelemetryStore
from link.packets import decode, encode
from link.udp import UdpLink

log = logging.getLogger("station")


class Station(QObject):
    changed = Signal()
    eventsChanged = Signal()

    FORWARD_KEYS = {"w", "up"}
    REVERSE_KEYS = {"s", "down"}
    LEFT_KEYS = {"a", "left"}
    RIGHT_KEYS = {"d", "right"}
    MOVEMENT_KEYS = FORWARD_KEYS | REVERSE_KEYS | LEFT_KEYS | RIGHT_KEYS

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.link = UdpLink(config["station_port"], config["rover_port"])
        self.telemetry = TelemetryStore()
        self._online = False
        self._armed = False
        self._left = self._right = 0.0
        self._speed = config["drive_speed"]
        self._seq = 0
        self._events = []
        self._invalid = 0

        self._stale_timeout = config.get("stale_after_ms", 1000) / 1000.0
        self._last_telemetry_time = None
        self._had_telemetry = False

        self._active_keys = set()
        self._mouse_active = False

        self._timer = QTimer(self)
        self._timer.setInterval(config["send_period_ms"])
        self._timer.timeout.connect(self.tick)
        self._timer.start()
        self.note("Station ready. Start the simulator, then connect.")

    @property
    def connection_state(self):
        if not self._online:
            return "disconnected"
        if self._last_telemetry_time is None:
            return "waiting"
        if time.monotonic() - self._last_telemetry_time > self._stale_timeout:
            return "stale"
        return "live"

    connectionState = Property(str, lambda self: self.connection_state, notify=changed)
    isLive = Property(bool, lambda self: self.connection_state == "live", notify=changed)
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
            self._last_telemetry_time = None
            self._had_telemetry = False
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
        self.clearKeys()
        self.stop()
        self._armed = False
        self.link.close()
        self._online = False
        self._last_telemetry_time = None
        self._had_telemetry = False
        self.note("Datalink closed")
        self.changed.emit()

    @Slot()
    def toggleArm(self):
        if not self._online:
            self.note("Connect before enabling drive", True)
            return
        self.clearKeys()
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
        self._mouse_active = True
        if not self._armed or not self._online:
            return
        if not (math.isfinite(left) and math.isfinite(right)):
            return
        self._left = max(-1.0, min(1.0, left)) * self._speed
        self._right = max(-1.0, min(1.0, right)) * self._speed
        self._send_drive()
        self.changed.emit()

    @Slot()
    def releaseMouse(self):
        self._mouse_active = False
        if self._active_keys:
            self._recompute_keyboard_drive()
        else:
            self.stop()

    @Slot(str, result=bool)
    def handleKeyPress(self, key_name):
        key = key_name.lower()
        if key not in self.MOVEMENT_KEYS:
            return False
        self._active_keys.add(key)
        if not self._mouse_active:
            self._recompute_keyboard_drive()
        return True

    @Slot(str, result=bool)
    def handleKeyRelease(self, key_name):
        key = key_name.lower()
        if key in self._active_keys:
            self._active_keys.remove(key)
            if not self._mouse_active:
                self._recompute_keyboard_drive()
            return True
        return False

    @Slot()
    def clearKeys(self):
        self._active_keys.clear()
        self._mouse_active = False
        if self._armed:
            self.stop()

    def _recompute_keyboard_drive(self):
        if not self._armed or not self._online:
            return

        if not any(k in self._active_keys for k in self.MOVEMENT_KEYS):
            self.stop()
            return

        fwd = 1 if any(k in self._active_keys for k in self.FORWARD_KEYS) else 0
        rev = 1 if any(k in self._active_keys for k in self.REVERSE_KEYS) else 0
        linear = fwd - rev

        left = 1 if any(k in self._active_keys for k in self.LEFT_KEYS) else 0
        right = 1 if any(k in self._active_keys for k in self.RIGHT_KEYS) else 0
        angular = left - right

        if linear == 0 and angular == 0:
            self.stop()
            return

        if linear != 0 and angular != 0:
            if linear > 0:
                l_drive = 0.0 if angular > 0 else 1.0
                r_drive = 1.0 if angular > 0 else 0.0
            else:
                l_drive = 0.0 if angular > 0 else -1.0
                r_drive = -1.0 if angular > 0 else 0.0
        elif linear != 0:
            l_drive = float(linear)
            r_drive = float(linear)
        else:
            l_drive = -float(angular)
            r_drive = float(angular)

        self._left = l_drive * self._speed
        self._right = r_drive * self._speed
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
        self._left = self._right = 0.0
        self._send_drive()
        self.changed.emit()

    @Slot()
    def tick(self):
        now = time.monotonic()
        prev_state = self.connection_state

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

                if packet.get("type") == "telemetry":
                    first = self._last_telemetry_time is None
                    self._last_telemetry_time = now
                    self._had_telemetry = True
                    self.telemetry.update(packet)
                    if first:
                        self.note("First rover telemetry received")

            curr_state = self.connection_state
            if curr_state != "live" and (self._left != 0.0 or self._right != 0.0 or self._active_keys):
                self.note(f"Telemetry not live (state: {curr_state}). Drive halted.", True)
                self.clearKeys()
                self.stop()

            if self._armed and curr_state == "live":
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
