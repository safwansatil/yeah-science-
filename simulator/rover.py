"""Simple differential drive, in metres and radians; explicit clock for tests."""
import math

WATCHDOG_SECONDS = 0.350


class Rover:
    def __init__(self):
        self.x = self.y = self.heading = 0.0
        self.left = self.right = 0.0
        self.battery = 12.6
        self.last_command = None
        self.failsafe = True

    def command(self, packet, now):
        if packet["type"] == "drive":
            self.left, self.right = packet["left"], packet["right"]
            self.last_command = now
            self.failsafe = False

    def step(self, now, dt):
        if self.last_command is None or now - self.last_command >= WATCHDOG_SECONDS:
            self.left = self.right = 0.0
            self.failsafe = True
        velocity = (self.left + self.right) * 0.5
        omega = (self.right - self.left) / 0.6
        mid = self.heading + omega * dt / 2
        self.x += velocity * math.cos(mid) * dt
        self.y += velocity * math.sin(mid) * dt
        self.heading = (self.heading + omega * dt) % (2 * math.pi)
        self.battery = max(10.5, self.battery - abs(velocity) * dt * 0.002)

    def telemetry(self):
        return {k: getattr(self, k) for k in ("x", "y", "heading", "left", "right", "battery", "failsafe")}
