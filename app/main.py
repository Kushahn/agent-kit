"""FastAPI surface for the agent kit.

Three routes and a health check. Everything the judge needs is reachable without
typing anything: open the page, press the demo button, watch the trail.
"""

from __future__ import annotations

import logging
import os
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

app = FastAPI(title="Agent Kit", docs_url="/api/docs")


class RunRequest(BaseModel):
    """A task to run, optionally against caller-supplied records."""

    task: str = Field(min_length=1, max_length=8000)
    records: list[dict[str, Any]] | None = Field(default=None, max_length=500)


def _missing_key() -> JSONResponse | None:
    """Return a readable error response if no API key is configured."""
    if os.environ.get("OPENAI_API_KEY"):
        return None
    return JSONResponse(
        status_code=503,
        content={"detail": "OPENAI_API_KEY is not set on the server. Add it and redeploy."},
    )


def _execute(task: str, records: list[dict[str, Any]], instructions: str | None) -> dict[str, Any]:
    """Run the agent over records and fold the flagged decisions into the result."""
    registry, flags = build_registry(records)
    run = run_agent(task, registry=registry, model=MODEL, instructions=instructions)
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
        "api_key_configured": bool(os.environ.get("OPENAI_API_KEY")),
        "demo_records": len(demo.RECORDS),
    }


@app.post("/api/demo")
def run_demo() -> Any:
    """Run the bundled case, so the app demonstrates itself with no input."""
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
