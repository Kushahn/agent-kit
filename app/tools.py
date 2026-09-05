"""Tool registry for the agent.

On hackathon day this is the file you gut. The registry is built per request and
closed over that request's data, so there is no shared mutable state to leak between
concurrent invocations on serverless.

Replace the three tools below with ones that speak the actual case. Keep the shape:
small functions, JSON-friendly returns, docstring-quality descriptions (the model
reads the description, so it is prompt engineering, not documentation).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

MAX_ROWS_RETURNED = 25


@dataclass
class Tool:
    """One callable exposed to the model, plus the schema it is advertised with."""

    name: str
    description: str
    parameters: dict[str, Any]
    fn: Callable[..., Any]

    def schema(self) -> dict[str, Any]:
        """Return the Responses API tool definition.

        Note the flat shape: the Responses API puts ``name`` at the top level,
        unlike chat.completions which nests it under ``function``.
        """
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


def build_registry(records: list[dict[str, Any]]) -> tuple[dict[str, Tool], list[dict[str, Any]]]:
    """Build a tool registry bound to one request's records.

    Args:
        records: The dataset the agent may inspect for this run.

    Returns:
        A ``(registry, flags)`` pair. ``flags`` is the live list the ``flag_record``
        tool appends to, so the caller can read the agent's decisions after the run.
    """
    flags: list[dict[str, Any]] = []

    def summarise() -> dict[str, Any]:
        columns = sorted({key for row in records for key in row})
        return {"row_count": len(records), "columns": columns, "sample": records[:3]}

    def query(field: str, equals: str | None = None, contains: str | None = None) -> dict[str, Any]:
        matched = []
        for row in records:
            value = str(row.get(field, ""))
            if equals is not None and value != equals:
                continue
            if contains is not None and contains.lower() not in value.lower():
                continue
            matched.append(row)
        return {"match_count": len(matched), "rows": matched[:MAX_ROWS_RETURNED]}

    def flag(record_id: str, reason: str, severity: str = "medium") -> dict[str, Any]:
        entry = {"record_id": record_id, "reason": reason, "severity": severity}
        flags.append(entry)
        return {"flagged": entry, "total_flagged": len(flags)}

    tools = [
        Tool(
            name="summarise_dataset",
            description=(
                "Return the row count, the column names and the first few rows of the "
                "dataset under review. Call this first to learn the data's shape."
            ),
            parameters={"type": "object", "properties": {}, "required": []},
            fn=summarise,
        ),
        Tool(
            name="query_records",
            description=(
                "Find rows where a column exactly equals a value, or contains a "
                "substring (case-insensitive). Use it to test a hypothesis about the data."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "field": {"type": "string", "description": "Column name to filter on."},
                    "equals": {"type": "string", "description": "Exact value to match."},
                    "contains": {"type": "string", "description": "Substring to look for."},
                },
                "required": ["field"],
            },
            fn=query,
        ),
        Tool(
            name="flag_record",
            description=(
                "Record a decision about one row, with a human-readable justification. "
                "This is the agent's output: call it for every row that warrants action."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "record_id": {"type": "string", "description": "Identifier of the row."},
                    "reason": {"type": "string", "description": "Why this row was flagged."},
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "How urgent the flag is.",
                    },
                },
                "required": ["record_id", "reason"],
            },
            fn=flag,
        ),
    ]
    return {tool.name: tool for tool in tools}, flags
