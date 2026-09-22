import unittest

from link.packets import decode, encode
from simulator.rover import Rover


class RoverTests(unittest.TestCase):
    def test_moves_from_received_command(self):
        rover = Rover()
        rover.command(decode(encode("drive", 1, left=1, right=1)), 0)
        rover.step(0.1, 0.1)
        self.assertAlmostEqual(rover.x, 0.1)
        self.assertEqual(rover.y, 0)

    def test_opposite_wheels_turn_without_translation(self):
        rover = Rover()
        rover.command(decode(encode("drive", 1, left=-1, right=1)), 0)
        rover.step(0.1, 0.1)
        self.assertGreater(rover.heading, 0)
        self.assertEqual((rover.x, rover.y), (0, 0))

    def test_watchdog_at_boundary(self):
        rover = Rover()
        rover.command(decode(encode("drive", 1, left=1, right=1)), 0)
        rover.step(0.349, 0.01)
        self.assertFalse(rover.failsafe)
        rover.step(0.350, 0.001)
        self.assertTrue(rover.failsafe)
        self.assertEqual((rover.left, rover.right), (0, 0))

    def test_hello_does_not_refresh_command_timeout(self):
        rover = Rover()
        rover.command(decode(encode("drive", 1, left=1, right=1)), 0)
        rover.command(decode(encode("hello", 2)), 0.3)
        rover.step(0.36, 0.01)
        self.assertTrue(rover.failsafe)

    def test_stop_applies_before_timeout(self):
        rover = Rover()
        rover.command(decode(encode("drive", 1, left=1, right=1)), 0)
        rover.command(decode(encode("drive", 2, left=0, right=0)), 0.1)
        self.assertEqual((rover.left, rover.right), (0, 0))
