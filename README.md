# agent-kit

A small, generic starting point for building a tool-calling AI agent that shows its work.

**Ingest data → an agent reasons over it with tools → an auditable decision you can export.**

The audit trail is the point. Most agent demos show you an answer; this shows every model
turn and every tool call that produced it, in order, with timings — which is what you
actually need to trust, debug, or evaluate an agent.

## Status and provenance

This is **plumbing, not a product.** It was written in September 2026 as personal
boilerplate ahead of a hackathon, deliberately kept generic so it carries no domain logic:
the tools in `app/tools.py` and the sample case in `app/demo.py` are placeholders meant to
be deleted and replaced. The commit history is public and dated so its origin is checkable.

## Run it

```bash
uv sync
uv run pytest -q                          # 7 tests, no API key needed
cp .env.example .env                      # add OPENAI_API_KEY
uv run uvicorn app.main:app --reload      # http://127.0.0.1:8000
```

Press **Run the demo case** — no input required.

## Layout

| Path | Role |
|---|---|
| `app/agent.py` | The loop: model turns, tool dispatch, trail capture, step and time budgets |
| `app/tools.py` | Tool registry, built per request and closed over that request's data |
| `app/demo.py` | A bundled case so the app demonstrates itself with no input |
| `app/main.py` | FastAPI: `/`, `/api/demo`, `/api/run`, `/api/health` |
| `app/ui.py` | Single page, inlined as a string constant |
| `tests/` | Smoke tests against an injected fake client — no network |

## Design notes

A few decisions that are deliberate rather than accidental:

- **The OpenAI client is injected**, so the whole loop is testable with no API key and no
  network. That is why the tests run anywhere.
- **No database.** The trail travels in the response and renders client-side. On serverless
  there is no persistent disk, and a database is the most likely thing to break a deploy.
- **Tool errors are returned to the model as text, not raised.** A bad call gets recovered
  from rather than ending the run.
- **Two budgets**: `MAX_STEPS` caps model turns so a loop cannot burn tokens, and
  `DEADLINE_SECONDS` stops the run before a serverless platform kills it mid-flight — a
  partial trail is far more useful than a gateway timeout.
- **No catch-all rewrite in `vercel.json`.** Vercel detects the FastAPI entrypoint natively;
  a `/(.*) → /api/index` rewrite rewrites the *path*, so every request arrives as
  `/api/index` and nothing routes. See `AGENTS.md`.

## Notes for AI coding agents

`AGENTS.md` is the source of truth for working on this repo. `CLAUDE.md` points at it, so
the two cannot drift apart.

## Licence

MIT — see `LICENSE`.
