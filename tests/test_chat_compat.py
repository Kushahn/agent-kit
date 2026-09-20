"""Tests for the chat.completions adapter.

The point being proved is that ``run_agent`` is untouched: the same loop, the same
registry and the same cost accounting run over a provider that has no Responses API.
No API key and no network - the inner client is a fake.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from app.agent import run_agent
from app.chat_compat import (
    AssistantText,
    ChatCompletionsClient,
    FunctionCall,
    to_chat_messages,
    to_chat_tools,
)
from app.tools import Tool


@dataclass
class FakeFn:
    name: str
    arguments: str


@dataclass
class FakeToolCall:
    id: str
    function: FakeFn
    type: str = "function"


class FakeMessage:
    """Stands in for a chat.completions choice message."""

    def __init__(self, content: str | None = None, tool_calls: list[Any] | None = None) -> None:
        self.content = content
        self.tool_calls = tool_calls


class FakeUsage:
    """chat.completions names its token fields differently from the Responses API."""

    def __init__(self, prompt_tokens: int, completion_tokens: int) -> None:
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens


class FakeCompletion:
    def __init__(self, message: FakeMessage, usage: FakeUsage | None = None) -> None:
        self.choices = [type("Choice", (), {"message": message})()]
        self.usage = usage


class FakeCompletions:
    def __init__(self, script: list[FakeCompletion]) -> None:
        self._script = script
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> FakeCompletion:
        self.calls.append(kwargs)
        return self._script[min(len(self.calls) - 1, len(self._script) - 1)]


class FakeChatClient:
    """Minimal stand-in for an OpenAI-compatible chat client (NVIDIA NIM, etc.)."""

    def __init__(self, script: list[FakeCompletion]) -> None:
        self.chat = type("Chat", (), {"completions": FakeCompletions(script)})()


def toy_registry() -> tuple[dict[str, Tool], list[Any]]:
    """A one-tool registry owned by this file, so cases cannot break these tests."""
    seen: list[Any] = []

    def echo(value: str) -> dict[str, Any]:
        seen.append(value)
        return {"echoed": value}

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


def test_tool_schemas_are_nested_under_function() -> None:
    """Responses puts name at the top level; chat.completions nests it. That is the bug."""
    registry, _ = toy_registry()

    converted = to_chat_tools([tool.schema() for tool in registry.values()])

    assert converted == [
        {
            "type": "function",
            "function": {
                "name": "echo",
                "description": "Echo a value back.",
                "parameters": {
                    "type": "object",
                    "properties": {"value": {"type": "string"}},
                    "required": ["value"],
                },
            },
        }
    ]


def test_tool_results_follow_the_assistant_message_that_asked_for_them() -> None:
    """chat.completions rejects a tool result that does not follow its tool_calls message."""
    conversation = [
        {"role": "user", "content": "do it"},
        FunctionCall(name="echo", arguments='{"value":"x"}', call_id="c1"),
        {"type": "function_call_output", "call_id": "c1", "output": "done"},
    ]

    messages = to_chat_messages(conversation, instructions="be terse")

    assert [m["role"] for m in messages] == ["system", "user", "assistant", "tool"]
    assert messages[2]["tool_calls"][0]["id"] == "c1"
    assert messages[2]["tool_calls"][0]["function"]["name"] == "echo"
    assert messages[3]["tool_call_id"] == "c1"
    assert messages[3]["content"] == "done"


def test_parallel_calls_share_one_assistant_message() -> None:
    """Two calls in one turn are one assistant message with two tool_calls, not two."""
    conversation = [
        {"role": "user", "content": "do both"},
        FunctionCall(name="echo", arguments="{}", call_id="c1"),
        FunctionCall(name="echo", arguments="{}", call_id="c2"),
        {"type": "function_call_output", "call_id": "c1", "output": "a"},
        {"type": "function_call_output", "call_id": "c2", "output": "b"},
    ]

    messages = to_chat_messages(conversation)

    assert [m["role"] for m in messages] == ["user", "assistant", "tool", "tool"]
    assert len(messages[1]["tool_calls"]) == 2


def test_assistant_prose_survives_the_round_trip() -> None:
    """Text echoed back into the conversation returns as an assistant message."""
    messages = to_chat_messages([AssistantText(text="thinking out loud")])

    assert messages == [{"role": "assistant", "content": "thinking out loud"}]


def test_run_agent_is_unchanged_over_chat_completions() -> None:
    """The whole point: same loop, same registry, same cost, no Responses API."""
    inner = FakeChatClient(
        [
            FakeCompletion(
                FakeMessage(tool_calls=[FakeToolCall(id="c1", function=FakeFn("echo", '{"value":"hi"}'))]),
                FakeUsage(1000, 200),
            ),
            FakeCompletion(FakeMessage(content="It echoed hi."), FakeUsage(1500, 300)),
        ]
    )
    registry, seen = toy_registry()

    run = run_agent("say hi", registry=registry, client=ChatCompletionsClient(inner), model="gpt-5.6")

    assert run.ok is True
    assert run.answer == "It echoed hi."
    assert seen == ["hi"], "the tool body actually ran"
    assert [step.kind for step in run.steps] == ["model", "tool", "model", "final"]
    # Token accounting survives the field rename (prompt/completion -> input/output).
    assert (run.tokens_in, run.tokens_out) == (2500, 500)
    assert run.to_dict()["cost_usd"] == pytest.approx(0.008125)
    # Second turn must carry the tool result back.
    assert [m["role"] for m in inner.chat.completions.calls[1]["messages"]] == [
        "user",
        "assistant",
        "tool",
    ]


def test_absent_usage_block_is_tolerated() -> None:
    """A provider that omits usage must not break a run."""
    inner = FakeChatClient([FakeCompletion(FakeMessage(content="Done."))])
    registry, _ = toy_registry()

    run = run_agent("go", registry=registry, client=ChatCompletionsClient(inner), model="nemotron")

    assert run.ok is True
    assert run.to_dict()["cost_usd"] == 0.0


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
