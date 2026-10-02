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
        self.assertEqual(self.station.linkState, "WAITING")

    def test_connect_without_telemetry_is_waiting(self):
        self.assertEqual(self.station.linkState, "WAITING")
        self.assertFalse(self.station.isLive)
        self.assertEqual(self.station.batteryText, "--")

    def test_valid_telemetry_establishes_live_state(self):
        self.station.link.incoming = [encode("telemetry", 0, x=1, y=2, heading=0,
                                            left=0.1, right=0.1, battery=12.6, failsafe=False)]
        self.station.tick()
        self.assertEqual(self.station.linkState, "LIVE")
        self.assertTrue(self.station.isLive)
        self.assertFalse(self.station.isStale)
        self.assertEqual(self.station.batteryText, "12.60")

    def test_stale_telemetry_triggers_stale_state_and_halts_motion(self):
        self.station.toggleArm()
        self.station.link.incoming = [encode("telemetry", 0, x=1, y=2, heading=0,
                                            left=0.1, right=0.1, battery=12.6, failsafe=False)]
        self.station.tick()
        self.station.handleKey("w", True)
        self.assertGreater(self.station.leftCommand, 0)

        # Simulate 1.5 seconds silence (exceeds stale_after_ms=1000)
        self.station.telemetry.received_at -= 1.5
        self.station.tick()
        self.assertEqual(self.station.linkState, "STALE")
        self.assertTrue(self.station.isStale)
        self.assertIn("[STALE]", self.station.batteryText)
        self.assertEqual(self.station.leftCommand, 0)

    def test_keyboard_driving_aliases_and_cancellation(self):
        self.station.toggleArm()
        self.station.handleKey("w", True)
        speed_w = self.station.leftCommand
        self.assertGreater(speed_w, 0)

        # Up is alias: holding both must not double speed
        self.station.handleKey("up", True)
        self.assertAlmostEqual(self.station.leftCommand, speed_w)

        # Release W: Up is still held, must not stop
        self.station.handleKey("w", False)
        self.assertAlmostEqual(self.station.leftCommand, speed_w)

        # Down is opposing: must cancel linear drive to zero
        self.station.handleKey("down", True)
        self.assertEqual(self.station.leftCommand, 0)
        self.assertEqual(self.station.rightCommand, 0)

        # Release all
        self.station.handleKey("up", False)
        self.station.handleKey("down", False)
        self.assertEqual(self.station.leftCommand, 0)

    def test_telemetry_recovery_does_not_silently_resume_movement(self):
        self.station.toggleArm()
        self.station.link.incoming = [encode("telemetry", 0, x=0, y=0, heading=0, left=0, right=0, battery=12, failsafe=False)]
        self.station.tick()
        self.station.handleKey("w", True)

        # Go stale
        self.station.telemetry.received_at -= 2.0
        self.station.tick()
        self.assertEqual(self.station.linkState, "STALE")

        # Recover with fresh valid telemetry
        self.station.link.incoming = [encode("telemetry", 1, x=0, y=0, heading=0, left=0, right=0, battery=12, failsafe=False)]
        self.station.tick()
        self.assertEqual(self.station.linkState, "LIVE")
        self.assertEqual(self.station.leftCommand, 0)
        self.assertEqual(self.station.rightCommand, 0)
