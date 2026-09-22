"""One UTF-8 JSON object per UDP datagram. See docs/protocol.md."""
import json
import math

MAX_PACKET = 2048
NUMBERS = (int, float)
TELEMETRY_FIELDS = ("x", "y", "heading", "left", "right", "battery")


def _number(value):
    return type(value) in NUMBERS and type(value) is not bool and math.isfinite(value)


def decode(raw):
    if not raw or len(raw) > MAX_PACKET:
        raise ValueError("Invalid packet size")
    try:
        packet = json.loads(raw)
    except (ValueError, TypeError, ArithmeticError, UnicodeError, RecursionError, OverflowError) as exc:
        raise ValueError("Invalid JSON") from exc
    if not isinstance(packet, dict) or type(packet.get("v")) is not int or packet["v"] != 1:
        raise ValueError("Unsupported packet version")
    if type(packet.get("seq")) is not int or packet["seq"] < 0:
        raise ValueError("Invalid sequence")
    kind = packet.get("type")
    if kind == "drive":
        if any(not _number(packet.get(k)) or not -1 <= packet[k] <= 1 for k in ("left", "right")):
            raise ValueError("Drive values must be finite and within [-1, 1]")
    elif kind == "telemetry":
        if any(not _number(packet.get(k)) for k in TELEMETRY_FIELDS):
            raise ValueError("Invalid telemetry values")
        if type(packet.get("failsafe")) is not bool:
            raise ValueError("Invalid failsafe flag")
    elif kind != "hello":
        raise ValueError("Unknown packet type")
    return packet


def encode(kind, seq, **fields):
    packet = dict(fields, v=1, type=kind, seq=seq)
    raw = json.dumps(packet, separators=(",", ":"), allow_nan=False).encode("utf-8")
    decode(raw)
    return raw
