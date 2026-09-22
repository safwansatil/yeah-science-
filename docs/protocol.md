# Local rover protocol

The station and simulator communicate over UDP on `127.0.0.1`. They are separate processes. These packets are for this exercise and are not compatible with Altair's real radios or firmware.

The default rover port is 45820; the station binds 45821. Both read `config/default.json` and optional `config/local.json`. Use the same configuration for both processes. Only packets from the configured peer address and port are accepted.

Each UDP datagram holds one complete UTF-8 JSON object, at most 2048 bytes. UDP preserves datagram boundaries: this is not a serial stream reassembly exercise. A datagram can still be lost. The decoder validates fields before they reach the model.

Every message has `v: 1`, a `type`, and a nonnegative integer `seq`. Sequence numbers are diagnostic counters, reset on process restart; this starter does not promise delivery or implement replay protection.

| Message | Fields | Meaning |
| --- | --- | --- |
| `hello` | Common fields only | Announces the station; does not command movement |
| `drive` | `left`, `right` | Wheel speed requests in [-1, 1], corresponding to m/s in this simulator |
| `telemetry` | `x`, `y`, `heading`, `left`, `right`, `battery`, `failsafe` | Rover position (m), heading (rad), applied wheel speeds (m/s), voltage (V), watchdog state (boolean) |

Example:

```json
{"v":1,"type":"drive","seq":8,"left":0.55,"right":0.55}
```

The station repeats commands every 50 ms while drive is enabled. Mouse release sends a zero command immediately. A lost stop packet is backed up by subsequent zero commands and by the rover watchdog: after 350 ms without a valid drive command, the simulator stops its wheels. Garbage and `hello` packets cannot reset that timer.

The simulator sends telemetry approximately ten times a second, even when stationary. It does so independently of the UI. Positive heading is counterclockwise; +X is right and +Y is up. Equal wheel speeds move straight; opposite signs rotate in place. The drawing uses 36 pixels per metre and may leave the view if you keep driving. Restart the simulator to reset its pose.

This is a teaching model with ideal wheel motion. It does not simulate terrain, inertia, radio propagation, a hardware emergency stop or collision avoidance.

## Reproducible scenarios

Run one simulator at a time. Stop it with Ctrl-C before changing scenarios.

```bash
python -m simulator
python -m simulator --scenario quiet
python -m simulator --scenario noise
python -m simulator --scenario dropout
```

- `normal`: regular valid telemetry.
- `quiet`: receives commands but sends no telemetry.
- `noise`: sends malformed bytes instead of telemetry.
- `dropout`: sends valid telemetry, goes silent between 4 and 8 seconds after startup, then resumes.

These scenarios affect telemetry only. To test lost drive commands and the rover watchdog, close the app, disable drive, or stop sending commands. `--duration N` makes the simulator exit after N seconds for scripted tests.
