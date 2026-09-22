"""FastAPI surface for the agent kit.

Three routes and a health check. Everything the judge needs is reachable without
typing anything: open the page, press the demo button, watch the trail.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from app import demo
from app.agent import DEFAULT_MODEL, run_agent
from app.tools import build_registry
from app.ui import PAGE

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

MODEL = os.environ.get("MODEL", DEFAULT_MODEL)
# "responses" (OpenAI) or "chat" (NVIDIA NIM and anything else OpenAI-compatible).
# Switching provider is this variable plus OPENAI_BASE_URL and OPENAI_API_KEY - no redeploy
# of code, no edit to the loop. See AGENTS.md, "If it is the OpenAI side that dies".
LLM_PROTOCOL = os.environ.get("LLM_PROTOCOL", "responses").lower()
# A real run of the demo case, saved from the page's export button. Served, clearly labelled,
# when no key is set: an expert who runs the repo without an API key still sees the main
# scenario (Regulations §5.4.16, §5.6.6). Located by this file, not the working directory.
RECORDING = Path(__file__).with_name("demo_recording.json")
# The value .env.example ships with. A copied-but-unedited .env must count as "no key".
PLACEHOLDER_KEY = "sk-..."

app = FastAPI(title="Agent Kit", docs_url="/api/docs")


class RunRequest(BaseModel):
    """A task to run, optionally against caller-supplied records."""

    task: str = Field(min_length=1, max_length=8000)
    records: list[dict[str, Any]] | None = Field(default=None, max_length=500)


def _build_client() -> Any | None:
    """Return a client for the configured protocol, or None to let the loop build one."""
    if LLM_PROTOCOL == "chat":
        from app.chat_compat import ChatCompletionsClient

        return ChatCompletionsClient()
    return None


def _has_key() -> bool:
    """Return True if a real-looking API key is configured."""
    return os.environ.get("OPENAI_API_KEY", "").strip() not in ("", PLACEHOLDER_KEY)


def _missing_key() -> JSONResponse | None:
    """Return a readable error response if no API key is configured."""
    if _has_key():
        return None
    return JSONResponse(
        status_code=503,
        content={
            "detail": "OPENAI_API_KEY is not set. Locally: put it in .env and start with "
            "`uvicorn app.main:app --env-file .env`. On Vercel: add it and redeploy."
        },
    )


def _replay() -> dict[str, Any] | None:
    """Return the recorded demo run when no key is set and a recording ships, else None."""
    if _has_key() or not RECORDING.is_file():
        return None
    payload = json.loads(RECORDING.read_text(encoding="utf-8"))
    payload["replayed"] = True
    return payload


def _execute(task: str, records: list[dict[str, Any]], instructions: str | None) -> dict[str, Any]:
    """Run the agent over records and fold the flagged decisions into the result."""
    registry, flags = build_registry(records)
    run = run_agent(task, registry=registry, client=_build_client(), model=MODEL, instructions=instructions)
    payload = run.to_dict()
    payload["flags"] = flags
    return payload


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    """Serve the single-page UI."""
    return HTMLResponse(PAGE)


@app.get("/api/health")
def health() -> dict[str, Any]:
    """Report deploy health. Judges and you both use this to confirm the box is alive."""
    return {
        "ok": True,
        "model": MODEL,
        "api_key_configured": _has_key(),
        "protocol": LLM_PROTOCOL,
        "base_url": os.environ.get("OPENAI_BASE_URL", "openai-default"),
        "demo_records": len(demo.RECORDS),
        "demo_recording": RECORDING.is_file(),
    }


@app.post("/api/demo")
def run_demo() -> Any:
    """Run the bundled case, so the app demonstrates itself with no input."""
    if (recorded := _replay()) is not None:
        return recorded
    if (err := _missing_key()) is not None:
        return err
    return _execute(demo.DEMO_TASK, demo.RECORDS, demo.INSTRUCTIONS)


@app.post("/api/run")
def run(request: RunRequest) -> Any:
    """Run a caller-supplied task, defaulting to the bundled records."""
    if (err := _missing_key()) is not None:
        return err
    records = request.records if request.records is not None else demo.RECORDS
    return _execute(request.task, records, demo.INSTRUCTIONS)
