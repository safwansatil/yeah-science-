# Yeah, Science.

This is a small ground station and a rover simulator. The station already has mouse controls, telemetry and a field view. Your work is to get comfortable in its repository, add keyboard driving and investigate a connection indicator that cannot quite be trusted.

You do not need a rover, a radio, a GPU or previous Qt experience. You will need Python, a desktop session and a willingness to look things up. AI tools are welcome. We want to understand the decisions you made and how you checked your work.

## Start here

1. Fork this repo and clone your fork.
2. Follow the setup below and drive the rover with the mouse.
3. Read [the two tasks](docs/tasks.md): **Better Call Git** and **Let Him Cook**.
4. Work on a branch, then open a PR back to this repo with your changes and explanation.

The starter has unfinished work on purpose. Keyboard driving is absent, the connection display needs attention, and there is some repository housekeeping. A launch problem unrelated to those tasks is something to ask us about, not something you need to struggle with silently.

## Setup

Use **Python 3.10–3.13**. Python 3.11 or 3.12 is a good default for the pinned Qt dependency. Run these commands from the repository root. Installing the requirements needs internet access; running the exercise afterwards does not.

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If you have another supported Python version, replace `-3.12`. Explicitly invoking the virtual environment's Python avoids needing to change PowerShell's activation policy.

Open two terminals in this folder:

```powershell
# Terminal 1
.\.venv\Scripts\python.exe -m simulator
```

```powershell
# Terminal 2
.\.venv\Scripts\python.exe -m app
```

### Ubuntu or macOS

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Open two terminals in the repository root and activate the environment in each:

```bash
# Terminal 1
source .venv/bin/activate
python -m simulator
```

```bash
# Terminal 2
source .venv/bin/activate
python -m app
```

On Ubuntu, if `venv` is unavailable, install `python3-venv`. A minimal desktop may also need Qt's system libraries:

```bash
sudo apt update
sudo apt install python3-venv libegl1 libopengl0 libxcb-cursor0 libxkbcommon-x11-0
```

A plain SSH terminal cannot display the window. WSL needs working graphical-app support; you can also run the desktop app on Windows and complete the Linux command work in Ubuntu. Keep the app and simulator in the same OS environment for this exercise. If your Mac's system Python is outside the supported range, install a supported version first.

## First run

Click **Connect**, then **Enable drive**. Hold Forward, Reverse, Left or Right. Release to stop. The small rover's position and the wheel readings come from telemetry sent by the simulator. Changing the speed slider affects the next mouse press. STOP requests zero speed while leaving drive enabled.

Open **Session notes** to try a text-entry panel. Notes currently last only while the app is open. No camera is needed: the field view is a simple visualisation of the simulator's reported pose.

Close the app normally or use Ctrl-C in its terminal. Stop the simulator with Ctrl-C in its own terminal. Restarting the simulator resets its position.

Now try connecting with the simulator stopped. That is the first bug report for Section 2. The remaining requirements and reproduction steps are in [docs/tasks.md](docs/tasks.md).

## Finding your way around

| Location | What is there |
| --- | --- |
| `app/__main__.py` | Starts Qt, loads configuration, wires up Python and QML |
| `app/` | Station coordination and the latest telemetry values |
| `qml/` | Window, mouse controls, telemetry cards, field view and notes panel |
| `link/` | Packet validation and local UDP transport |
| `simulator/` | Separate rover process, wheel motion and command timeout |
| `config/default.json` | Shared default ports, command rate and settings |
| `scripts/` | Shell launcher and local diagnostic tool |
| `runtime/` | Local logs and a leftover synthetic bench log |
| `tests/` | Baseline tests for existing behaviour |
| `docs/` | Tasks, packet format and learning resources |

The coordinator has accumulated several responsibilities. Follow a working mouse command through it before deciding what to change. You do not need to understand every file before making progress.

All traffic stays on loopback. This is newly written teaching code inspired by our work on rover interfaces and communication links. It does not contain the team's private applications or their real configuration, and it is not intended to control hardware.

## Checks and diagnostics

With the virtual environment active (or its Python path on Windows):

```bash
python -m unittest discover -s tests -v
python scripts/doctor.py
```

The baseline tests should pass on the starter. They verify existing behaviour, not the features you have been asked to implement. Add a regression check for your connection fix and test keyboard interactions in the actual window too.

With the simulator running and the app **closed**, this probe waits for valid telemetry:

```bash
python scripts/doctor.py --probe
```

It temporarily uses the station port, so it cannot run alongside the app. Its exit code is 0 for a valid reply and 1 for failure. The probe does not command motion.

For controlled communication failures, see [the simulator scenarios](docs/protocol.md#reproducible-scenarios). No real network scanning or radio configuration is required.

## Common setup problems

- **`No module named PySide6`:** install the requirements using the same Python executable that starts the app. `doctor.py` prints that executable.
- **Address already in use:** another station, simulator or probe may still be running. Close the old process. If needed, make an ignored `config/local.json` with different `rover_port` and `station_port` values and restart both processes.
- **Qt cannot load its platform plugin:** check that you have a desktop session and the Ubuntu libraries listed above. Do not change application logic to work around a missing system library.
- **Permission denied for `./scripts/launch.sh`:** investigate its file permissions as part of Section 1. You can use `python -m app` while you work on that.
- **The permission change does not appear in Git:** use a Linux filesystem for this exercise where possible. A Windows-hosted checkout may not detect Unix executable-bit changes; check the file mode in Git's index as well.
- **Connected, but nothing moves:** make sure the simulator is running with matching ports, use the normal scenario, and enable drive. Remember that investigating the meaning of "connected" is part of your task.

## Making your work reviewable

Use small commits when you finish a meaningful change. In your PR, explain what works, how you tested it and anything still incomplete. Link your explanation if it lives elsewhere. A recording, writing, slides or another format is fine; help us follow the work without having to guess.

You are allowed to be unfamiliar with this stack. If you get stuck, show us the command or action, the output and what you have already tried. That is useful engineering work too.

[Task details](docs/tasks.md) · [Resources](docs/resources.md) · [Packet format](docs/protocol.md)
