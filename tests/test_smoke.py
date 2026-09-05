"""The one check that has to pass before you build on this.

Runs the whole loop with a fake client, so it needs no API key and no network -
which matters, because at the venue you want this green before you wire a key.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from app.agent import run_agent
from app.tools import build_registry

RECORDS = [
    {"id": "R-1", "name": "alpha", "amount": 10},
    {"id": "R-2", "name": "beta", "amount": 20},
]


@dataclass
class FakeCall:
    """Stands in for a Responses API function_call output item."""

    name: str
    arguments: str
    call_id: str = "call_1"
    type: str = "function_call"


class FakeResponse:
    """Stands in for a Responses API result."""

    def __init__(self, output: list[Any], text: str = "") -> None:
        self.output = output
        self.output_text = text


class FakeResponses:
    """Replays a scripted list of responses, one per create() call."""

    def __init__(self, script: list[FakeResponse]) -> None:
        self._script = script
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> FakeResponse:
        self.calls.append(kwargs)
        return self._script[min(len(self.calls) - 1, len(self._script) - 1)]


class FakeClient:
    """Minimal stand-in for the OpenAI client."""

    def __init__(self, script: list[FakeResponse]) -> None:
        self.responses = FakeResponses(script)


def test_loop_calls_tool_then_answers() -> None:
    """A tool call is executed, fed back, and the final answer is captured."""
    client = FakeClient(
        [
            FakeResponse([FakeCall(name="summarise_dataset", arguments="{}")]),
            FakeResponse([], text="There are 2 records."),
        ]
    )
    registry, _flags = build_registry(RECORDS)

    run = run_agent("describe the data", registry=registry, client=client, model="fake")

    assert run.ok is True
    assert run.answer == "There are 2 records."
    kinds = [step.kind for step in run.steps]
    assert kinds == ["model", "tool", "model", "final"]
    # The tool actually ran against the injected records, not a stub.
    assert "row_count" in run.steps[1].detail and "2" in run.steps[1].detail
    # The tool result was fed back to the model as a function_call_output.
    second_input = client.responses.calls[1]["input"]
    assert any(isinstance(item, dict) and item.get("type") == "function_call_output" for item in second_input)


def test_flags_are_collected() -> None:
    """flag_record decisions surface through the shared flags list."""
    client = FakeClient(
        [
            FakeResponse([FakeCall(name="flag_record", arguments='{"record_id":"R-2","reason":"outlier"}')]),
            FakeResponse([], text="Flagged one record."),
        ]
    )
    registry, flags = build_registry(RECORDS)

    run_agent("find outliers", registry=registry, client=client, model="fake")

    assert flags == [{"record_id": "R-2", "reason": "outlier", "severity": "medium"}]


def test_unknown_tool_does_not_raise() -> None:
    """An unknown tool becomes an error string the model can recover from."""
    client = FakeClient(
        [
            FakeResponse([FakeCall(name="does_not_exist", arguments="{}")]),
            FakeResponse([], text="Recovered."),
        ]
    )
    registry, _flags = build_registry(RECORDS)

    run = run_agent("do a thing", registry=registry, client=client, model="fake")

    assert run.ok is True
    assert "no such tool" in run.steps[1].detail


def test_bad_arguments_do_not_raise() -> None:
    """Malformed tool arguments are reported, not raised."""
    client = FakeClient(
        [
            FakeResponse([FakeCall(name="query_records", arguments="{not json")]),
            FakeResponse([], text="Recovered."),
        ]
    )
    registry, _flags = build_registry(RECORDS)

    run = run_agent("query", registry=registry, client=client, model="fake")

    assert "not valid JSON" in run.steps[1].detail


def test_step_budget_is_enforced() -> None:
    """A model that never stops calling tools is cut off, not left to burn tokens."""
    client = FakeClient([FakeResponse([FakeCall(name="summarise_dataset", arguments="{}")])])
    registry, _flags = build_registry(RECORDS)

    run = run_agent("loop forever", registry=registry, client=client, model="fake", max_steps=3)

    assert run.ok is False
    assert run.steps[-1].name == "max_steps"


def test_model_failure_is_recorded_not_raised() -> None:
    """An API failure ends the run cleanly with the reason visible in the trail."""

    class Exploding:
        def create(self, **_: Any) -> Any:
            raise RuntimeError("api is down")

    class Client:
        responses = Exploding()

    registry, _flags = build_registry(RECORDS)

    run = run_agent("anything", registry=registry, client=Client(), model="fake")

    assert run.ok is False
    assert "api is down" in run.steps[0].detail


def test_deadline_returns_partial_trail() -> None:
    """Out of wall-clock time, the run returns what it has instead of being killed."""
    client = FakeClient([FakeResponse([FakeCall(name="summarise_dataset", arguments="{}")])])
    registry, _flags = build_registry(RECORDS)

    run = run_agent("slow work", registry=registry, client=client, model="fake", deadline_s=0.0)

    assert run.ok is False
    assert run.steps[-1].name == "deadline"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
