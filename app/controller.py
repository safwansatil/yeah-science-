"""Station coordinator. Input, transport and display state meet here.

This class has grown with the UI; there is room to separate responsibilities
when someone next changes it. Keep the mouse controls working while doing so.
"""
import logging
import math
import time

from PySide6.QtCore import QObject, Property, QTimer, Signal, Slot, Qt

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
        self._keyboard_pressed = False
        self.held_keys = []
        self.link = UdpLink(config["station_port"], config["rover_port"])
        self.telemetry = TelemetryStore()
        self._online = False
        self.stale_after_ms = config["stale_after_ms"]
        self._armed = False
        self._left = self._right = 0.0
        self._speed = config["drive_speed"]
        self._seq = 0
        self._events = []
        self.stale_count = 0
        self._invalid = 0
        self._timer = QTimer(self) #this creates a QTimer object that will be used to periodically call the tick method, which handles receiving packets and updating the telemetry data.
        self._timer.setInterval(config["send_period_ms"]) #sets the interval for the timer based on the configuration value "send_period_ms", which determines how often the tick method will be called.
        self._timer.timeout.connect(self.tick)  #this connects the timeout signal of the timer to the tick method, so that tick is called every time the timer times out.
        self._timer.start()  #start the timer, which will call the tick method at the specified interval.
        self.note("Station ready. Start the simulator, then connect.")

    connected = Property(bool, lambda self: self._online, notify=changed)
    keyboard_pressed = Property(bool, lambda self: self._keyboard_pressed, notify=changed)
    connection_status = Property(str, lambda self: self.telemetry.status(self.stale_after_ms, self._online), notify=changed)
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
            self.link.send(encode("hello", self._seq))
            self._seq += 1
            self.note("Datalink opened on port " + str(self.config["station_port"]))
        except OSError as exc:
            self.link.close()
            self._online = False
            self.note("Cannot open link: " + str(exc), True)
        self.changed.emit()

    @Slot(int)
    def pressedkey(self, key):
        if key not in self.held_keys:
            self.held_keys.append(key)
            self._keyboard_pressed = True
            if len(self.held_keys) == 1:
                self.stop()
            else:
                self.changed.emit()

    @Slot(int)
    def releasedkey(self, key):
        if key in self.held_keys:
            self.held_keys.remove(key)
            self._keyboard_pressed = bool(self.held_keys)
            if not self.held_keys:
                self.stop()
            else:
                self.changed.emit()

    @Slot(list)
    def keylogic(self, held_keys):

        if not self._armed or not self._online:
            return
        if not held_keys:
            self.stop()
            return
        
        move_precedence = 0
        turn_precedence = 0
        if held_keys[0] == 87 or held_keys[0] == 83 or held_keys[0] == Qt.Key.Key_Up or held_keys[0] == Qt.Key.Key_Down:
            move_precedence = 1
        elif held_keys[0] == 65 or held_keys[0] == 68 or held_keys[0] == Qt.Key.Key_Left or held_keys[0] == Qt.Key.Key_Right:
            turn_precedence = 1
        if move_precedence == 1:
            move = (87 in held_keys or Qt.Key.Key_Up in held_keys) - (83 in held_keys or Qt.Key.Key_Down in held_keys)
            turn = 0
        if turn_precedence == 1:
            turn = (68 in held_keys or Qt.Key.Key_Right in held_keys) - (65 in held_keys or Qt.Key.Key_Left in held_keys)
            move = 0


        l = max(-1.0, min(1.0, move + turn))
        r = max(-1.0, min(1.0, move - turn))

        if l == 0 and r == 0:
            self.stop()
        else:
            self.setDrive(l, r)


    @Slot()
    def disconnectLink(self):
        self.stop()
        self._armed = False
        self.link.close()
        self.clearinput()
        self._online = False
        self.note("Datalink closed")
        self.changed.emit()



    @Slot()
    def toggleArm(self):
        if not self._online:
            self.note("Connect before enabling drive", True)
            return
        self.stop()
        self.clearinput()
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
    def clearinput(self):
        self.held_keys = []
        self._keyboard_pressed = False
        self.changed.emit()

    @Slot()
    def stop(self):
        self._left = self._right = 0.0
        self._send_drive()
        self.changed.emit()

    @Slot()
    def tick(self): #tick method is called periodically by the QTimer to handle receiving packets and updating the telemetry data.
        if self._online:
            try:
                packets = self.link.receive() #receive packets, store in packets variable
            except OSError as exc:
                self.note("Receive failed: " + str(exc), True) #warning.logging if receive fails
                self.disconnectLink() #then disconnect the link and return from the tick method.
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
            if self.held_keys:
                self.keylogic(self.held_keys)
            self.stale_count += 1
            if self.telemetry.status(self.stale_after_ms, self._online) == "Stale":
                self.held_keys = []
                if self.stale_count == 1 or self.stale_count % 100 == 0:
                    self.note(f"Telemetry is stale (no valid telemetry for {time.monotonic() - self.telemetry.received_at: .2f}s)", True)
            else:
                self.stale_count = 0

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
