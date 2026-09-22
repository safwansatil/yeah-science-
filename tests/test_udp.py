import socket
import time
import unittest

from link.udp import UdpLink


class TransportTests(unittest.TestCase):
    def test_real_loopback_and_sender_filter(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as peer, socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as stranger:
            peer.bind(("127.0.0.1", 0))
            peer.settimeout(1)
            link = UdpLink(0, peer.getsockname()[1])
            try:
                link.open()
                target = link.socket.getsockname()
                link.send(b"outgoing")
                self.assertEqual(peer.recvfrom(1024)[0], b"outgoing")
                stranger.sendto(b"wrong sender", target)
                peer.sendto(b"incoming", target)
                received = []
                deadline = time.monotonic() + 1
                while time.monotonic() < deadline and not received:
                    received.extend(link.receive())
                    time.sleep(0.005)
                self.assertEqual(received, [b"incoming"])
            finally:
                link.close()

    def test_bind_conflict_has_clear_failure(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as occupied:
            occupied.bind(("127.0.0.1", 0))
            link = UdpLink(occupied.getsockname()[1], 45820)
            with self.assertRaises(OSError):
                link.open()
            self.assertIsNone(link.socket)
