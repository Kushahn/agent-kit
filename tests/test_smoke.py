"""Loop tests. These must survive gutting `app/tools.py` for a new case.

Deliberately built on a local throwaway registry rather than the real one: the loop's
contract (dispatch, feed results back, budgets, error handling) is independent of whichever
tools a given case needs. Case-specific tools get their own tests in test_case.py.

Runs with a fake client, so no API key and no network.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from app.agent import run_agent
from app.tools import Tool


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


def toy_registry() -> tuple[dict[str, Tool], list[Any]]:
    """A two-tool registry owned by this test file, so cases cannot break these tests."""
    seen: list[Any] = []

    def echo(value: str) -> dict[str, Any]:
        seen.append(value)
        return {"echoed": value, "count": len(seen)}

    tools = {
        "echo": Tool(
            name="echo",
            description="Echo a value back.",
            parameters={
                "type": "object",
                "properties": {"value": {"type": "string"}},
                "required": ["value"],
            },
            fn=echo,
        )
    }
    return tools, seen


def test_loop_calls_tool_then_answers() -> None:
    """A tool call is executed, fed back, and the final answer is captured."""
    client = FakeClient(
        [
            FakeResponse([FakeCall(name="echo", arguments='{"value":"hello"}')]),
            FakeResponse([], text="It echoed hello."),
        ]
    )
    registry, seen = toy_registry()

    run = run_agent("say hello", registry=registry, client=client, model="fake")

    assert run.ok is True
    assert run.answer == "It echoed hello."
    assert [step.kind for step in run.steps] == ["model", "tool", "model", "final"]
    assert seen == ["hello"], "the tool body actually ran"
    # The result was fed back as a function_call_output on the next turn.
    second_input = client.responses.calls[1]["input"]
    assert any(isinstance(item, dict) and item.get("type") == "function_call_output" for item in second_input)


def test_unknown_tool_does_not_raise() -> None:
    """An unknown tool becomes an error string the model can recover from."""
    client = FakeClient(
        [
            FakeResponse([FakeCall(name="does_not_exist", arguments="{}")]),
            FakeResponse([], text="Recovered."),
        ]
    )
    registry, _ = toy_registry()

    run = run_agent("do a thing", registry=registry, client=client, model="fake")

    assert run.ok is True
    assert "no such tool" in run.steps[1].detail


def test_bad_arguments_do_not_raise() -> None:
    """Malformed tool arguments are reported, not raised."""
    client = FakeClient(
        [
            FakeResponse([FakeCall(name="echo", arguments="{not json")]),
            FakeResponse([], text="Recovered."),
        ]
    )
    registry, _ = toy_registry()

    run = run_agent("echo", registry=registry, client=client, model="fake")

    assert "not valid JSON" in run.steps[1].detail


def test_tool_exception_is_reported_not_raised() -> None:
    """A tool that throws is reported back to the model instead of ending the run."""

    def explode() -> dict[str, Any]:
        raise ValueError("tool blew up")

    registry = {
        "boom": Tool("boom", "Explodes.", {"type": "object", "properties": {}, "required": []}, explode)
    }
    client = FakeClient(
        [FakeResponse([FakeCall(name="boom", arguments="{}")]), FakeResponse([], text="Recovered.")]
    )

    run = run_agent("break it", registry=registry, client=client, model="fake")

    assert run.ok is True
    assert "ValueError: tool blew up" in run.steps[1].detail


def test_step_budget_is_enforced() -> None:
    """A model that never stops calling tools is cut off, not left to burn tokens."""
    client = FakeClient([FakeResponse([FakeCall(name="echo", arguments='{"value":"x"}')])])
    registry, _ = toy_registry()

    run = run_agent("loop forever", registry=registry, client=client, model="fake", max_steps=3)

    assert run.ok is False
    assert run.steps[-1].name == "max_steps"


def test_deadline_returns_partial_trail() -> None:
    """Out of wall-clock time, the run returns what it has instead of being killed."""
    client = FakeClient([FakeResponse([FakeCall(name="echo", arguments='{"value":"x"}')])])
    registry, _ = toy_registry()

    run = run_agent("slow work", registry=registry, client=client, model="fake", deadline_s=0.0)

    assert run.ok is False
    assert run.steps[-1].name == "deadline"


def test_model_failure_is_recorded_not_raised() -> None:
    """An API failure ends the run cleanly with the reason visible in the trail."""

    class Exploding:
        def create(self, **_: Any) -> Any:
            raise RuntimeError("api is down")

    class Client:
        responses = Exploding()

    registry, _ = toy_registry()

    run = run_agent("anything", registry=registry, client=Client(), model="fake")

    assert run.ok is False
    assert "api is down" in run.steps[0].detail


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
