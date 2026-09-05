# AGENTS.md — the contract

Single source of truth for both agents. `CLAUDE.md` points here. Written so **either
Claude or Codex can drive this project alone**, because one of them may hit a usage
limit mid-build.

## What this project is

Ingest unknown data → a tool-calling agent reasons over it → an **auditable decision**.
The audit trail is the product, not a debug aid: HackAlem AI judges *agentic* solutions,
and a visible chain of tool calls is the evidence. An AI judge reads it first.

## Layout

| Path | Role |
|---|---|
| `app/agent.py` | The loop. Model turns, tool dispatch, trail capture. Rarely changes. |
| `app/tools.py` | **Gut this on the day.** Tools are the case-specific part. |
| `app/demo.py` | **Gut this on the day.** The bundled case the demo button runs. |
| `app/main.py` | FastAPI routes. Rarely changes. |
| `app/ui.py` | The page, inlined as a string constant. |
| `api/index.py` | Vercel entrypoint shim. Do not move. |
| `tests/test_smoke.py` | Runs the whole loop with a fake client — no API key needed. |

## Division of labour

**Claude defines interfaces. Codex fills bodies. Claude reviews.**
Never point both at the same file at the same time.

- **Claude** — reads the case, picks the track, writes tool *signatures and descriptions*,
  wires modules, writes the README and the pitch, keeps `PROGRESS.md` current, reviews.
- **Codex** — implements one self-contained file per task against a fixed signature.
  Owning whole files is what prevents collisions.

Delegate like this:

```bash
codex exec -p hackathon -s workspace-write --approve-for-me -C . -o .codex/last.md "<task>"
codex review          # before submitting
```

`-p hackathon` loads `~/.codex/hackathon.config.toml`: reasoning effort `high`, plugins off.
Measured: **45s vs 2m36s** against the default `ultra` profile on a real coding task. Use
`-c model_reasoning_effort="ultra"` for a single genuinely hard problem, not as the default.

Keep `.codex/` committed. Codex use is mandatory (§8.6 lets experts verify it) and the
session logs are the evidence.

## Non-negotiable rules on the day

1. **Commit at least once an hour.** Regulations §6.6: a missing hour is grounds for
   disqualification. Append a line to `PROGRESS.md` each time.
2. **Deploy at hour 0, not hour 5.** §8.9 rejects undeployed projects before judging.
   An empty live URL early beats a perfect local app.
3. **Disclose pre-existing code.** §6.4. This scaffold is public and predates the event —
   say so in the README and in the first commit message.
4. **All work in the organiser's repo.** §6.8.
5. **Feature freeze at hour 3.** The rubric rewards a small working thing, explained well.
6. Production code quality is **explicitly not judged** (§7.4). Ship ugly, ship working.

## Adding a tool

Tools are prompt engineering: the model reads the `description`, so write it for the model.

```python
Tool(
    name="verb_noun",
    description="What it returns and when to call it. Be concrete.",
    parameters={"type": "object", "properties": {...}, "required": [...]},
    fn=callable_returning_json_friendly_data,
)
```

Registry is built per request and closed over that request's data — no module globals,
so nothing leaks between concurrent serverless invocations.

## Commands

```bash
uv sync                                   # install
uv run pytest -q                          # must be green before building on it
uv run uvicorn app.main:app --reload      # local, http://127.0.0.1:8000
vercel --prod                             # deploy
```

## Conventions

Python 3.12+, type hints on every signature, Google-style docstrings on public functions,
`pathlib` over `os.path`, `logging` never `print`, constants UPPER_SNAKE_CASE at module top.
Conventional commits (`feat:`, `fix:`, `chore:`, `docs:`).
