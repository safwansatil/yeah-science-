"""Non-blocking loopback transport. Socket ownership belongs to the caller."""
import socket


class UdpLink:
    def __init__(self, local_port, peer_port):
        self.local_port = local_port
        self.peer = ("127.0.0.1", peer_port)
        self.socket = None
        self.rx = self.tx = 0

    def open(self):
        if self.socket:
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.bind(("127.0.0.1", self.local_port))
            sock.setblocking(False)
        except OSError:
            sock.close()
            raise
        self.socket = sock

    def send(self, raw):
        if self.socket is None:
            raise OSError("Socket is closed")
        self.tx += self.socket.sendto(raw, self.peer)

    def receive(self):
        if self.socket is None:
            return []
        packets = []
        # Bound each poll so incoming traffic cannot monopolise the UI thread.
        for _ in range(64):
            try:
                raw, sender = self.socket.recvfrom(65535)
            except (BlockingIOError, ConnectionResetError):
                break
            if sender == self.peer:
                self.rx += len(raw)
                packets.append(raw)
        return packets

    def close(self):
        if self.socket:
            self.socket.close()
            self.socket = None
