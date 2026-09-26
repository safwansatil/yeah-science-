import unittest
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication, Qt

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

    def test_connection_states_waiting_live_stale_and_recovery(self):
        # Connecting without simulator replies starts in 'waiting', not 'live'
        self.assertEqual(self.station.connectionState, "waiting")
        self.assertFalse(self.station.telemetryFresh)
        self.assertEqual(self.station.displayTelemetry["battery"], "--")

        # Arbitrary noise bytes do not establish live state
        self.station.link.incoming = [b"corrupted-bytes"]
        self.station.tick()
        self.assertEqual(self.station.connectionState, "waiting")

        # Valid telemetry transitions to 'live'
        self.station.link.incoming = [encode("telemetry", 1, x=1.5, y=2.0, heading=0.0,
                                             left=0.55, right=0.55, battery=12.5, failsafe=False)]
        self.station.tick()
        self.assertEqual(self.station.connectionState, "live")
        self.assertTrue(self.station.telemetryFresh)
        self.assertEqual(self.station.displayTelemetry["battery"], "12.50")

        # Start driving with keyboard, then let telemetry go stale (> 1000 ms)
        self.station.toggleArm()
        self.station.keyPress(Qt.Key.Key_W)
        self.assertAlmostEqual(self.station.leftCommand, 0.55)

        self.station.telemetry.received_at -= 1.5
        self.station.tick()
        self.assertEqual(self.station.connectionState, "stale")
        self.assertFalse(self.station.telemetryFresh)
        self.assertEqual(self.station.displayTelemetry["battery"], "STALE")
        # Stale telemetry stops active movement immediately
        self.assertEqual(self.station.leftCommand, 0.0)
        self.assertEqual(self.station.rightCommand, 0.0)

        # Recovery restores 'live' telemetry without silently resuming old movement
        self.station.link.incoming = [encode("telemetry", 2, x=1.6, y=2.0, heading=0.0,
                                             left=0.0, right=0.0, battery=12.4, failsafe=True)]
        self.station.tick()
        self.assertEqual(self.station.connectionState, "live")
        self.assertTrue(self.station.telemetryFresh)
        self.assertEqual(self.station.leftCommand, 0.0)
        self.assertEqual(self.station.rightCommand, 0.0)

    def test_keyboard_driving_aliases_cancellation_and_autorepeat(self):
        self.station.toggleArm()

        # W and Up are aliases: holding both does not double speed, releasing one keeps moving
        self.station.keyPress(Qt.Key.Key_W)
        self.station.keyPress(Qt.Key.Key_Up)
        self.assertAlmostEqual(self.station.leftCommand, 0.55)
        self.assertAlmostEqual(self.station.rightCommand, 0.55)

        # Auto-repeat release/press is ignored
        self.station.keyRelease(Qt.Key.Key_W, True)
        self.assertAlmostEqual(self.station.leftCommand, 0.55)

        # Releasing W while Up is still held does not stop
        self.station.keyRelease(Qt.Key.Key_W, False)
        self.assertAlmostEqual(self.station.leftCommand, 0.55)

        # Opposing directions cancel (Up + Down = 0)
        self.station.keyPress(Qt.Key.Key_Down)
        self.assertEqual(self.station.leftCommand, 0.0)
        self.assertEqual(self.station.rightCommand, 0.0)
        self.station.keyRelease(Qt.Key.Key_Down)
        self.assertAlmostEqual(self.station.leftCommand, 0.55)

        # Releasing the last key stops immediately
        self.station.keyRelease(Qt.Key.Key_Up)
        self.assertEqual(self.station.leftCommand, 0.0)
        self.assertEqual(self.station.rightCommand, 0.0)
        self.assertEqual(self.station.link.sent[-1]["left"], 0.0)

    def test_session_notes_and_focus_loss_clear_keyboard_drive(self):
        self.station.toggleArm()
        self.station.keyPress(Qt.Key.Key_W)
        self.assertAlmostEqual(self.station.leftCommand, 0.55)

        # Opening session notes stops rover and blocks typing from moving rover
        self.station.setNotesOpen(True)
        self.assertEqual(self.station.leftCommand, 0.0)
        self.station.keyPress(Qt.Key.Key_D)
        self.assertEqual(self.station.leftCommand, 0.0)

        # Closing session notes does not resume movement without fresh input
        self.station.setNotesOpen(False)
        self.assertEqual(self.station.leftCommand, 0.0)
