"""A Responses-shaped adapter over the chat.completions API.

The organisers issue $50 of NVIDIA credit alongside the OpenAI credit, and NVIDIA NIM
(``https://integrate.api.nvidia.com/v1``) speaks chat.completions - it does not serve the
Responses API that ``app.agent`` calls. Pointing ``OPENAI_BASE_URL`` at it would 404 every
turn, and §8.9 rejects a project that does not run.

Rather than branch the loop, this presents the small slice of the Responses surface that
``run_agent`` actually touches: ``client.responses.create(...)`` returning an object with
``output``, ``output_text`` and ``usage``. ``app/agent.py`` is therefore unchanged and
untestable-by-provider: flip ``LLM_PROTOCOL=chat`` and the same loop runs on either.

ponytail: covers the one shape this loop uses - no streaming, no images, no structured
outputs. Add them only if a case needs them.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"


@dataclass
class FunctionCall:
    """A tool call, shaped like the Responses API item ``app.agent`` looks for."""

    name: str
    arguments: str
    call_id: str
    type: str = "function_call"


@dataclass
class AssistantText:
    """Assistant prose, kept in ``output`` so it survives the conversation round trip."""

    text: str
    type: str = "message"


@dataclass
class Usage:
    """Token counts under the Responses API's field names, which ``agent`` reads."""

    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class ChatResponse:
    """The subset of a Responses result that the loop consumes."""

    output: list[Any] = field(default_factory=list)
    output_text: str = ""
    usage: Usage = field(default_factory=Usage)


def to_chat_tools(schemas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert flat Responses tool schemas into the nested chat.completions shape.

    Args:
        schemas: Tool definitions as produced by ``app.tools.Tool.schema``.

    Returns:
        The same tools with name, description and parameters nested under ``function``.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": schema["name"],
                "description": schema.get("description", ""),
                "parameters": schema.get("parameters", {}),
            },
        }
        for schema in schemas
    ]


def to_chat_messages(conversation: list[Any], instructions: str | None = None) -> list[dict[str, Any]]:
    """Flatten the loop's mixed conversation list into chat.completions messages.

    The loop accumulates three kinds of item: plain role dicts, the ``output`` items from
    a previous turn, and ``function_call_output`` dicts. Chat completions requires the
    assistant message carrying ``tool_calls`` to appear *before* the tool results that
    answer it, so pending calls are flushed the moment anything else arrives.

    Args:
        conversation: The loop's running list of turns.
        instructions: Optional system-level steer, sent as a leading system message.

    Returns:
        A message list the chat.completions endpoint accepts.
    """
    messages: list[dict[str, Any]] = []
    if instructions:
        messages.append({"role": "system", "content": instructions})
    pending: list[FunctionCall] = []

    def flush() -> None:
        if not pending:
            return
        messages.append(
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": call.call_id,
                        "type": "function",
                        "function": {"name": call.name, "arguments": call.arguments},
                    }
                    for call in pending
                ],
            }
        )
        pending.clear()

    for item in conversation:
        if isinstance(item, FunctionCall):
            pending.append(item)
            continue
        flush()
        if isinstance(item, AssistantText):
            if item.text:
                messages.append({"role": "assistant", "content": item.text})
        elif isinstance(item, dict) and item.get("type") == "function_call_output":
            messages.append({"role": "tool", "tool_call_id": item["call_id"], "content": item["output"]})
        elif isinstance(item, dict) and "role" in item:
            messages.append(item)
        else:  # An item from a real Responses client, which this adapter never produced.
            logger.warning("dropping unconvertible conversation item: %r", type(item))
    flush()
    return messages


class _Responses:
    """The ``.responses`` attribute of the adapter, exposing only ``create``."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def create(
        self,
        *,
        model: str,
        tools: list[dict[str, Any]] | None = None,
        # Shadows a builtin deliberately: the Responses API names this parameter `input`,
        # and the loop calls it by keyword.
        input: list[Any],
        instructions: str | None = None,
    ) -> ChatResponse:
        """Run one chat.completions turn and return it in Responses shape."""
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": to_chat_messages(input, instructions),
        }
        if tools:
            kwargs["tools"] = to_chat_tools(tools)

        completion = self._client.chat.completions.create(**kwargs)
        message = completion.choices[0].message

        output: list[Any] = []
        text = getattr(message, "content", None) or ""
        if text:
            output.append(AssistantText(text=text))
        for call in getattr(message, "tool_calls", None) or []:
            output.append(
                FunctionCall(
                    name=call.function.name,
                    arguments=call.function.arguments or "{}",
                    call_id=call.id,
                )
            )

        raw = getattr(completion, "usage", None)
        usage = Usage(
            input_tokens=int(getattr(raw, "prompt_tokens", 0) or 0),
            output_tokens=int(getattr(raw, "completion_tokens", 0) or 0),
        )
        return ChatResponse(output=output, output_text=text, usage=usage)


class ChatCompletionsClient:
    """Drop-in stand-in for the OpenAI client that speaks chat.completions underneath.

    Args:
        client: An OpenAI-compatible client. Defaults to a real ``OpenAI()`` pointed at
            ``OPENAI_BASE_URL``, or at NVIDIA NIM when that variable is unset.
    """

    def __init__(self, client: Any | None = None) -> None:
        if client is None:
            from openai import OpenAI  # imported lazily so tests need no API key

            client = OpenAI(base_url=os.environ.get("OPENAI_BASE_URL", NVIDIA_BASE_URL))
        self.responses = _Responses(client)
