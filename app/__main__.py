"""Run from the repository root: python -m app."""
import argparse
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import signal
import sys

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow

from app.config import ROOT, load_config
from app.controller import Station


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", help="Optional JSON overrides")
    parser.add_argument("--quit-after", type=float, default=0, help="Exit after N seconds for a smoke check")
    parser.add_argument("--screenshot", help="Save the window at exit (use with --quit-after)")
    args = parser.parse_args()
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
    runtime = ROOT / "runtime"
    runtime.mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                        handlers=[logging.StreamHandler(), RotatingFileHandler(runtime / "station.log", maxBytes=500000, backupCount=2, encoding="utf-8")])
    qt = QGuiApplication([sys.argv[0]])
    qt.setApplicationName("Yeah, Science — Altair")
    engine = QQmlApplicationEngine()
    station = Station(load_config(args.config))
    engine.rootContext().setContextProperty("station", station)
    engine.load(QUrl.fromLocalFile(str(ROOT / "qml/Main.qml")))
    if not engine.rootObjects():
        station.shutdown()
        return 1
    window = engine.rootObjects()[0]
    qt.aboutToQuit.connect(station.shutdown)
    signal.signal(signal.SIGINT, lambda *_: qt.quit())
    signal.signal(signal.SIGTERM, lambda *_: qt.quit())
    # A Python timer callback gives the interpreter time to process Ctrl-C.
    signal_timer = QTimer()
    signal_timer.timeout.connect(lambda: None)
    signal_timer.start(200)

    def finish():
        try:
            if args.screenshot:
                path = Path(args.screenshot)
                path.parent.mkdir(parents=True, exist_ok=True)
                if not window.grabWindow().save(str(path)):
                    logging.error("Could not save screenshot")
        finally:
            qt.quit()

    if args.quit_after > 0:
        QTimer.singleShot(int(args.quit_after * 1000), finish)
    return qt.exec()


if __name__ == "__main__":
    sys.exit(main())
