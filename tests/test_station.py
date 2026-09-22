import unittest
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication

from app.config import load_config
from app.controller import Station
from link.packets import decode, encode

QT = QCoreApplication.instance() or QCoreApplication([])


class MemoryLink:
    def __init__(self, *args):
        self.rx = self.tx = 0
        self.sent = []
        self.incoming = []

    def open(self):
        pass

    def close(self):
        pass

    def send(self, raw):
        self.sent.append(decode(raw))
        self.tx += len(raw)

    def receive(self):
        result, self.incoming = self.incoming, []
        return result


class StationTests(unittest.TestCase):
    def setUp(self):
        with patch("app.controller.UdpLink", MemoryLink):
            self.station = Station(load_config())
        self.station._timer.stop()
        self.station.connectLink()

    def tearDown(self):
        self.station.shutdown()

    def test_drive_requires_arming(self):
        self.station.setDrive(1, 1)
        self.assertEqual(self.station.leftCommand, 0)
        self.station.toggleArm()
        self.station.setDrive(1, -1)
        self.assertAlmostEqual(self.station.link.sent[-1]["left"], 0.55)
        self.assertAlmostEqual(self.station.link.sent[-1]["right"], -0.55)

    def test_release_sends_zero_immediately(self):
        self.station.toggleArm()
        self.station.setDrive(1, 1)
        self.station.stop()
        self.assertEqual(self.station.link.sent[-1]["left"], 0)
        self.assertEqual(self.station.link.sent[-1]["right"], 0)

    def test_reconnect_does_not_restore_drive(self):
        self.station.toggleArm()
        self.station.setDrive(1, 1)
        self.station.disconnectLink()
        self.station.connectLink()
        self.assertFalse(self.station.armed)
        self.assertEqual(self.station.leftCommand, 0)

    def test_display_values_come_from_telemetry(self):
        self.station.link.incoming = [encode("telemetry", 0, x=3, y=1, heading=0,
                                            left=0.2, right=0.3, battery=12.4, failsafe=False)]
        self.station.tick()
        self.assertEqual(self.station.telemetryData["x"], 3)
        self.assertEqual(self.station.telemetryData["battery"], 12.4)

    def test_noise_does_not_replace_telemetry(self):
        self.station.link.incoming = [b"noise"]
        self.station.tick()
        self.assertEqual(self.station.invalidPackets, 1)
        self.assertIsNone(self.station.telemetry.received_at)
