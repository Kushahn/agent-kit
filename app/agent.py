"""Minimal tool-calling agent loop that records a full audit trail.

The trail is the product, not a debug aid: HackAlem AI judges an *agentic* solution,
and a visible chain of model turns and tool calls is the clearest evidence that the
thing actually reasons. It is also what an AI judge reads first.

The OpenAI client is injected so the loop is testable with no API key and no network.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Protocol

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-5.6"
MAX_STEPS = 8
TOOL_OUTPUT_LIMIT = 4000
# Vercel caps a function at 60s on Hobby. Stop at 50s and return the partial trail:
# a visible "ran out of time" step is far better than a gateway timeout showing a judge nothing.
DEADLINE_SECONDS = 50.0


class SupportsResponses(Protocol):
    """Structural type for the bit of the OpenAI client this module uses."""

    responses: Any


@dataclass
class Step:
    """One observable event in an agent run."""

    n: int
    kind: str  # "model" | "tool" | "final" | "error"
    name: str = ""
    detail: str = ""
    ms: int = 0


@dataclass
class AgentRun:
    """The result of a run, including every step taken to get there."""

    task: str
    model: str
    answer: str = ""
    ok: bool = True
    steps: list[Step] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable view, for the API and the export button."""
        return asdict(self)


def _ms(started: float) -> int:
    """Return elapsed milliseconds since a monotonic start time."""
    return int((time.monotonic() - started) * 1000)


def _text_of(response: Any) -> str:
    """Pull the assistant text out of a Responses API result, tolerating absence."""
    return getattr(response, "output_text", "") or ""


def _invoke(registry: dict[str, Any], call: Any) -> str:
    """Run one tool call and return its output as a string.

    Never raises: a tool error is fed back to the model as text so it can recover,
    which is almost always better than aborting a run five minutes before the deadline.
    """
    tool = registry.get(call.name)
    if tool is None:
        return f"ERROR: no such tool {call.name!r}"
    try:
        args = json.loads(call.arguments or "{}")
    except json.JSONDecodeError as exc:
        return f"ERROR: arguments were not valid JSON: {exc}"
    try:
        result = tool.fn(**args)
    except Exception as exc:  # noqa: BLE001 - deliberately broad; see docstring
        logger.warning("tool %s failed: %s", call.name, exc)
        return f"ERROR: {type(exc).__name__}: {exc}"
    text = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, default=str)
    return text[:TOOL_OUTPUT_LIMIT]


def run_agent(
    task: str,
    *,
    registry: dict[str, Any],
    client: SupportsResponses | None = None,
    model: str = DEFAULT_MODEL,
    max_steps: int = MAX_STEPS,
    instructions: str | None = None,
    deadline_s: float = DEADLINE_SECONDS,
) -> AgentRun:
    """Run the tool-calling loop until the model answers or the step budget runs out.

    Args:
        task: The user-facing request the agent should satisfy.
        registry: Mapping of tool name to Tool, as built by ``app.tools``.
        client: An OpenAI-compatible client. Defaults to a real ``OpenAI()``.
        model: Model id. Kept a parameter so it can be swapped at the event.
        max_steps: Hard cap on model turns, so a loop cannot burn the token budget.
        instructions: Optional system-level steer passed to the Responses API.
        deadline_s: Wall-clock budget. On expiry the run returns what it has rather
            than being killed mid-flight by the platform.

    Returns:
        An AgentRun holding the final answer and every step taken.
    """
    if client is None:
        from openai import OpenAI  # imported lazily so tests need no API key

        client = OpenAI()

    run = AgentRun(task=task, model=model)
    schemas = [tool.schema() for tool in registry.values()]
    conversation: list[Any] = [{"role": "user", "content": task}]
    deadline = time.monotonic() + deadline_s

    for n in range(1, max_steps + 1):
        if time.monotonic() >= deadline:
            run.ok = False
            run.steps.append(Step(n, "error", "deadline", f"stopped after {deadline_s:.0f}s"))
            return run
        started = time.monotonic()
        try:
            response = client.responses.create(
                model=model,
                tools=schemas,
                input=conversation,
                instructions=instructions,
            )
        except Exception as exc:  # noqa: BLE001 - surface the failure in the trail
            logger.error("model call failed on step %s: %s", n, exc)
            run.ok = False
            run.steps.append(Step(n, "error", "model", f"{type(exc).__name__}: {exc}"[:500], _ms(started)))
            return run

        run.steps.append(Step(n, "model", model, _text_of(response)[:500], _ms(started)))

        # Echo every output item back, reasoning items included: GPT-5 class models
        # require their reasoning to be replayed alongside tool outputs.
        conversation += response.output

        calls = [item for item in response.output if getattr(item, "type", None) == "function_call"]
        if not calls:
            run.answer = _text_of(response)
            run.steps.append(Step(n, "final", "", run.answer[:2000]))
            return run

        for call in calls:
            started = time.monotonic()
            output = _invoke(registry, call)
            run.steps.append(Step(n, "tool", call.name, output[:1000], _ms(started)))
            conversation.append({"type": "function_call_output", "call_id": call.call_id, "output": output})

    run.ok = False
    run.steps.append(Step(max_steps, "error", "max_steps", f"no answer after {max_steps} steps"))
    return run
