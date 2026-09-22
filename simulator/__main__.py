"""python -m simulator [--scenario quiet|noise|dropout]"""
import argparse
import logging
import socket
import time

from app.config import load_config
from link.packets import decode, encode
from simulator.rover import Rover


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config")
    parser.add_argument("--scenario", choices=("normal", "quiet", "noise", "dropout"), default="normal")
    parser.add_argument("--duration", type=float, default=0, help="Exit after N seconds (0: until Ctrl-C)")
    args = parser.parse_args()
    config = load_config(args.config)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    rover = Rover()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((config["host"], config["rover_port"]))
        sock.setblocking(False)
        peer = (config["host"], config["station_port"])
        logging.info("SIM listening on %s:%s scenario=%s", *sock.getsockname(), args.scenario)
        started = previous = last_tx = time.monotonic()
        seq = 0
        last_failsafe = True
        try:
            while not args.duration or time.monotonic() - started < args.duration:
                now = time.monotonic()
                for _ in range(64):
                    try:
                        raw, sender = sock.recvfrom(65535)
                    except (BlockingIOError, ConnectionResetError):
                        break
                    if sender != peer:
                        continue
                    try:
                        packet = decode(raw)
                    except ValueError as exc:
                        logging.warning("DROP invalid command: %s", exc)
                        continue
                    rover.command(packet, now)
                rover.step(now, min(now - previous, 0.1))
                previous = now
                if rover.failsafe != last_failsafe:
                    logging.info("WATCHDOG %s", "stopped wheels" if rover.failsafe else "valid drive received")
                    last_failsafe = rover.failsafe
                if now - last_tx >= 0.1:
                    elapsed = now - started
                    silent = args.scenario == "quiet" or (args.scenario == "dropout" and 4 <= elapsed < 8)
                    if not silent:
                        raw = b"radio-noise" if args.scenario == "noise" else encode("telemetry", seq, **rover.telemetry())
                        sock.sendto(raw, peer)
                        seq += 1
                    last_tx = now
                time.sleep(0.01)
        except KeyboardInterrupt:
            logging.info("SIM stopped by operator")


if __name__ == "__main__":
    main()
