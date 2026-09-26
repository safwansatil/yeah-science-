"""Station coordinator. Input, transport and display state meet here.

This class has grown with the UI; there is room to separate responsibilities
when someone next changes it. Keep the mouse controls working while doing so.
"""
import logging
import math
import time

from PySide6.QtCore import QObject, Property, QTimer, Qt, Signal, Slot

from app.telemetry import TelemetryStore
from link.packets import decode, encode
from link.udp import UdpLink

log = logging.getLogger("station")

KEY_ALIASES = {
    "w": "w",
    "up": "up",
    "s": "s",
    "down": "down",
    "a": "a",
    "left": "left",
    "d": "d",
    "right": "right",
    int(Qt.Key.Key_W): "w",
    int(Qt.Key.Key_Up): "up",
    int(Qt.Key.Key_S): "s",
    int(Qt.Key.Key_Down): "down",
    int(Qt.Key.Key_A): "a",
    int(Qt.Key.Key_Left): "left",
    int(Qt.Key.Key_D): "d",
    int(Qt.Key.Key_Right): "right",
}


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
        self._left = self._right = 0.0
        self._speed = config["drive_speed"]
        self._seq = 0
        self._events = []
        self._invalid = 0
        self._held_keys = set()
        self._mouse_active = False
        self._notes_open = False
        self._was_stale = False
        self._timer = QTimer(self)
        self._timer.setInterval(config["send_period_ms"])
        self._timer.timeout.connect(self.tick)
        self._timer.start()
        self.note("Station ready. Start the simulator, then connect.")

    def _connection_state(self, now=None):
        if not self._online:
            return "disconnected"
        if self.telemetry.received_at is None:
            return "waiting"
        if self.telemetry.is_stale(self.config["stale_after_ms"], now=now):
            return "stale"
        return "live"

    def _connection_label(self):
        state = self._connection_state()
        if state == "disconnected":
            return "DISCONNECTED"
        if state == "waiting":
            return "WAITING FOR REPLY"
        if state == "stale":
            return "STALE TELEMETRY"
        return "LIVE TELEMETRY"

    def _display_telemetry(self):
        state = self._connection_state()
        if state in ("disconnected", "waiting"):
            return {k: "--" for k in ("x", "y", "heading", "left", "right", "battery", "failsafe")}
        if state == "stale":
            return {k: "STALE" for k in ("x", "y", "heading", "left", "right", "battery", "failsafe")}
        return {
            "x": f"{self.telemetry.values['x']:.2f}",
            "y": f"{self.telemetry.values['y']:.2f}",
            "heading": f"{self.telemetry.values['heading'] * 180.0 / math.pi:.0f}",
            "left": f"{self.telemetry.values['left']:.2f}",
            "right": f"{self.telemetry.values['right']:.2f}",
            "battery": f"{self.telemetry.values['battery']:.2f}",
            "failsafe": "holding stop" if self.telemetry.values["failsafe"] else "receiving commands",
        }

    connected = Property(bool, lambda self: self._online, notify=changed)
    connectionState = Property(str, lambda self: self._connection_state(), notify=changed)
    connectionLabel = Property(str, lambda self: self._connection_label(), notify=changed)
    telemetryFresh = Property(bool, lambda self: self._connection_state() == "live", notify=changed)
    displayTelemetry = Property("QVariantMap", lambda self: self._display_telemetry(), notify=changed)
    armed = Property(bool, lambda self: self._armed, notify=changed)
    notesOpen = Property(bool, lambda self: self._notes_open, notify=changed)
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
            self.telemetry.reset()
            self._was_stale = False
            self._held_keys.clear()
            self._mouse_active = False
            self._online = True
            self.link.send(encode("hello", self._seq))
            self._seq += 1
            self.note("Datalink opened on port " + str(self.config["station_port"]) + " (waiting for rover telemetry)")
        except OSError as exc:
            self.link.close()
            self._online = False
            self.note("Cannot open link: " + str(exc), True)
        self.changed.emit()

    @Slot()
    def disconnectLink(self):
        self.stop()
        self._armed = False
        self._was_stale = False
        self.telemetry.reset()
        self.link.close()
        self._online = False
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
            if self._held_keys and not self._mouse_active and self._armed and self._online:
                self._apply_keyboard_drive()
            self.changed.emit()

    @Slot(float, float)
    def setDrive(self, left, right):
        if not self._armed or not self._online:
            return
        if not (math.isfinite(left) and math.isfinite(right)):
            return
        # Mouse pad input overrides and clears any held keyboard keys
        self._held_keys.clear()
        self._mouse_active = (left != 0.0 or right != 0.0)
        self._left = max(-1.0, min(1.0, left)) * self._speed
        self._right = max(-1.0, min(1.0, right)) * self._speed
        self._send_drive()
        self.changed.emit()

    def _normalize_key(self, key):
        if isinstance(key, str):
            return KEY_ALIASES.get(key.strip().lower())
        try:
            return KEY_ALIASES.get(int(key))
        except (TypeError, ValueError):
            return None

    @Slot("QVariant", result=bool)
    def isDriveKey(self, key):
        return self._normalize_key(key) is not None

    @Slot("QVariant")
    @Slot("QVariant", bool)
    def keyPress(self, key, auto_repeat=False):
        if auto_repeat:
            return
        if not self._online or not self._armed or self._notes_open:
            return
        norm = self._normalize_key(key)
        if norm is None:
            return
        self._mouse_active = False
        self._held_keys.add(norm)
        self._apply_keyboard_drive()

    @Slot("QVariant")
    @Slot("QVariant", bool)
    def keyRelease(self, key, auto_repeat=False):
        if auto_repeat:
            return
        norm = self._normalize_key(key)
        if norm is None or norm not in self._held_keys:
            return
        self._held_keys.discard(norm)
        if not self._mouse_active:
            self._apply_keyboard_drive()

    def _apply_keyboard_drive(self):
        if not self._online or not self._armed or self._notes_open or not self._held_keys:
            self._left = self._right = 0.0
            self._send_drive()
            self.changed.emit()
            return

        forward = ("w" in self._held_keys) or ("up" in self._held_keys)
        reverse = ("s" in self._held_keys) or ("down" in self._held_keys)
        left = ("a" in self._held_keys) or ("left" in self._held_keys)
        right = ("d" in self._held_keys) or ("right" in self._held_keys)

        throttle = (1.0 if forward else 0.0) - (1.0 if reverse else 0.0)
        turn = (1.0 if right else 0.0) - (1.0 if left else 0.0)

        if throttle == 0.0 and turn == 0.0:
            raw_left, raw_right = 0.0, 0.0
        elif throttle != 0.0 and turn == 0.0:
            raw_left, raw_right = throttle, throttle
        elif throttle == 0.0 and turn != 0.0:
            raw_left, raw_right = turn, -turn
        else:
            # Forward/reverse + turn curves smoothly by scaling the inner wheel
            if turn > 0.0:
                raw_left, raw_right = throttle, throttle * 0.5
            else:
                raw_left, raw_right = throttle * 0.5, throttle

        self._left = max(-1.0, min(1.0, raw_left)) * self._speed
        self._right = max(-1.0, min(1.0, raw_right)) * self._speed
        self._send_drive()
        self.changed.emit()

    @Slot(bool)
    def setNotesOpen(self, is_open):
        self._notes_open = bool(is_open)
        if self._notes_open:
            self.stop()
        else:
            self.changed.emit()

    @Slot()
    def focusLost(self):
        self.stop()

    def _send_drive(self):
        if not self._online:
            return
        try:
            self.link.send(encode("drive", self._seq, left=self._left, right=self._right))
            self._seq += 1
        except OSError as exc:
            self.note("Send failed: " + str(exc), True)
            self._held_keys.clear()
            self._mouse_active = False
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
                    was_stale = self._was_stale or (
                        not first and self.telemetry.is_stale(self.config["stale_after_ms"])
                    )
                    self.telemetry.update(packet)
                    if first:
                        self.note("First rover telemetry received")
                    elif was_stale:
                        self._was_stale = False
                        # Never silently resume an old movement after telemetry recovery
                        self._held_keys.clear()
                        self._mouse_active = False
                        self._left = self._right = 0.0
                        self.note("Telemetry recovered — require fresh input to move")

            if self.telemetry.received_at is not None and self.telemetry.is_stale(self.config["stale_after_ms"]):
                if not self._was_stale:
                    self._was_stale = True
                    self.note("Telemetry stale — stopping drive", True)
                    self.stop()

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
