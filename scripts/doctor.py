"""Read-only local checks: python scripts/doctor.py [--probe]."""
import argparse
import importlib.util
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import load_config
from link.packets import decode, encode
from link.udp import UdpLink


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", action="store_true", help="Close the app first; listen for rover telemetry for two seconds")
    parser.add_argument("--config")
    args = parser.parse_args()
    print("Python:", sys.version.split()[0])
    print("Executable:", sys.executable)
    has_qt = importlib.util.find_spec("PySide6") is not None
    print("PySide6:", "available" if has_qt else "missing; install requirements.txt")
    try:
        config = load_config(args.config)
    except (OSError, ValueError) as exc:
        print("CONFIG ERROR:", exc)
        return 1
    print("Station port:", config["station_port"], " Rover port:", config["rover_port"])
    if not args.probe:
        print("No packets sent. Add --probe with the app closed to check the simulator.")
        return 0 if has_qt else 1
    link = UdpLink(config["station_port"], config["rover_port"])
    try:
        link.open()
        link.send(encode("hello", 0))
        deadline = time.monotonic() + 2
        invalid = 0
        while time.monotonic() < deadline:
            for raw in link.receive():
                try:
                    packet = decode(raw)
                except ValueError:
                    invalid += 1
                    continue
                if packet["type"] == "telemetry":
                    print("ROVER REPLY: telemetry sequence", packet["seq"])
                    return 0
            time.sleep(0.02)
        print(f"NO TELEMETRY: received {link.rx} bytes, rejected {invalid} malformed packets.")
        print("Check simulator process, matching config and scenario. No hardware is involved.")
        return 1
    except OSError as exc:
        print("SOCKET ERROR:", exc)
        print("Close the station before probing; only one process can own its port.")
        return 1
    finally:
        link.close()


if __name__ == "__main__":
    sys.exit(main())
