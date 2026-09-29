"""Regression tests for the station's connection-state machine."""
import time

import pytest

from app.telemetry import ConnectionState, TelemetryStore


def _packet(seq=0):
    return {
        "v": 1, "type": "telemetry", "seq": seq,
        "x": 0.0, "y": 0.0, "heading": 0.0,
        "left": 0.0, "right": 0.0, "battery": 12.6, "failsafe": False,
    }


def test_initial_state_is_disconnected():
    store = TelemetryStore(stale_after_ms=1000)
    assert store.state == ConnectionState.DISCONNECTED


def test_link_opened_moves_to_waiting():
    store = TelemetryStore(stale_after_ms=1000)
    store.on_link_opened()
    assert store.state == ConnectionState.WAITING


def test_valid_packet_moves_to_live():
    store = TelemetryStore(stale_after_ms=1000)
    store.on_link_opened()
    store.update(_packet(seq=1))
    assert store.state == ConnectionState.LIVE


def test_quiet_scenario_stays_waiting():
    """Simulator --scenario quiet: link open but no telemetry ever arrives."""
    store = TelemetryStore(stale_after_ms=100)
    store.on_link_opened()
    time.sleep(0.2)
    changed = store.tick()
    assert store.state == ConnectionState.WAITING
    assert changed is False


def test_noise_scenario_never_reaches_live():
    """Simulator --scenario noise: garbage bytes never call update()."""
    store = TelemetryStore(stale_after_ms=100)
    store.on_link_opened()
    time.sleep(0.2)
    store.tick()
    assert store.state == ConnectionState.WAITING


def test_dropout_scenario_transitions_to_stale():
    """Simulator --scenario dropout: data stops, then resumes."""
    store = TelemetryStore(stale_after_ms=100)
    store.on_link_opened()
    store.update(_packet(seq=1))
    assert store.state == ConnectionState.LIVE

    time.sleep(0.15)
    changed = store.tick()
    assert changed is True
    assert store.state == ConnectionState.STALE


def test_dropout_recovery_returns_to_live():
    store = TelemetryStore(stale_after_ms=100)
    store.on_link_opened()
    store.update(_packet(seq=1))
    time.sleep(0.15)
    store.tick()
    assert store.state == ConnectionState.STALE

    store.update(_packet(seq=2))
    assert store.state == ConnectionState.LIVE


def test_link_closed_resets_to_disconnected():
    store = TelemetryStore(stale_after_ms=1000)
    store.on_link_opened()
    store.update(_packet(seq=1))
    store.on_link_closed()
    assert store.state == ConnectionState.DISCONNECTED
    assert store.received_at is None
    assert store.sequence is None


def test_tick_is_noop_when_not_live():
    store = TelemetryStore(stale_after_ms=100)
    assert store.tick() is False
    store.on_link_opened()
    assert store.tick() is False


def test_stale_resets_on_new_packet():
    store = TelemetryStore(stale_after_ms=100)
    store.on_link_opened()
    store.update(_packet(seq=1))
    time.sleep(0.15)
    store.tick()
    assert store.state == ConnectionState.STALE
    store.update(_packet(seq=2))
    assert store.state == ConnectionState.LIVE
    time.sleep(0.05)
    store.tick()
    assert store.state == ConnectionState.LIVE