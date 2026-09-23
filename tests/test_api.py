"""HTTP-level checks for what a judge without an API key sees.

Hackathons commonly drop a project that will not run from its README, and a judge may
have no key. These pin the two no-key outcomes: a labelled replay, or a readable 503.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main


@pytest.fixture
def no_key(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """A client against a server with no API key configured."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    return TestClient(main.app)


def test_demo_without_key_or_recording_explains_the_fix(
    no_key: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """No key and no recording: a 503 that names the --env-file step, not a crash."""
    monkeypatch.setattr(main, "RECORDING", tmp_path / "missing.json")

    response = no_key.post("/api/demo")

    assert response.status_code == 503
    assert "--env-file" in response.json()["detail"]


def test_demo_without_key_replays_the_recording_labelled(
    no_key: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """No key but a recording ships: the recorded run comes back, marked as a replay."""
    recording = tmp_path / "demo_recording.json"
    recording.write_text(json.dumps({"ok": True, "answer": "recorded", "steps": []}), encoding="utf-8")
    monkeypatch.setattr(main, "RECORDING", recording)

    response = no_key.post("/api/demo")

    assert response.status_code == 200
    assert response.json()["replayed"] is True
    assert response.json()["answer"] == "recorded"
    assert no_key.get("/api/health").json()["demo_recording"] is True


def test_the_example_placeholder_counts_as_no_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """A .env copied from .env.example unedited must not look like a configured key."""
    monkeypatch.setenv("OPENAI_API_KEY", main.PLACEHOLDER_KEY)

    assert TestClient(main.app).get("/api/health").json()["api_key_configured"] is False


def test_a_set_key_never_serves_the_recording(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """With a key set, a stale recording must not stand in for a live run."""
    recording = tmp_path / "demo_recording.json"
    recording.write_text(json.dumps({"answer": "recorded"}), encoding="utf-8")
    monkeypatch.setattr(main, "RECORDING", recording)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    assert main._replay() is None
