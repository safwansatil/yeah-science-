"""Load defaults, then an optional machine-local override."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_config(path=None):
    config = json.loads((ROOT / "config/default.json").read_text(encoding="utf-8"))
    local = Path(path) if path else ROOT / "config/local.json"
    if path or local.exists():
        config.update(json.loads(local.read_text(encoding="utf-8")))
    if config["host"] != "127.0.0.1":
        raise ValueError("This exercise uses loopback only: host must be 127.0.0.1")
    for name in ("rover_port", "station_port"):
        if type(config[name]) is not int or not 1024 <= config[name] <= 65535:
            raise ValueError(f"Invalid {name}")
    if config["rover_port"] == config["station_port"]:
        raise ValueError("Rover and station need different ports")
    if type(config["drive_speed"]) not in (int, float) or not 0 < config["drive_speed"] <= 1:
        raise ValueError("drive_speed must be in (0, 1]")
    for name in ("send_period_ms", "stale_after_ms"):
        if type(config[name]) is not int or not 20 <= config[name] <= 10000:
            raise ValueError(f"Invalid {name}")
    if config["send_period_ms"] >= 350:
        raise ValueError("Send period must be shorter than the rover watchdog")
    return config
