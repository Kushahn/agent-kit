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
| `vercel.json` | Function config only. **Never add a catch-all rewrite** — see Deploy. |
| `tests/test_smoke.py` | Loop tests on a **throwaway registry** — they survive gutting `tools.py`. |
| `tests/test_case.py` | Write case-specific tool tests here on the day. |

## Division of labour

**Claude defines interfaces. Codex fills bodies. Claude reviews.**
Never point both at the same file at the same time.

- **Claude** — reads the case, picks the track, writes tool *signatures and descriptions*,
  wires modules, writes the README and the pitch, keeps `PROGRESS.md` current, reviews.
- **Codex** — implements one self-contained file per task against a fixed signature.
  Owning whole files is what prevents collisions.

Delegate like this:

```bash
# Delegate. NOTE: --approve-for-me already implies the workspace-write sandbox and
# CONFLICTS with -s; passing both fails instantly with an argument error.
codex exec -p hackathon --approve-for-me -C . -o .codex/last.md "<task>"

# Review. -p must come BEFORE the subcommand, and a range is required.
codex exec -p hackathon review --base <commit>      # or --uncommitted
```

Run delegations in the foreground, or check the output file afterwards. A backgrounded
`codex exec` that fails on its arguments exits in under a second and the error is easy
to miss — exactly how the broken command above survived until the dress rehearsal.

`-p hackathon` loads `~/.codex/hackathon.config.toml`: reasoning effort `high`, plugins off.
Measured: **45s vs 2m36s** against the default `ultra` profile on a real coding task. Use
`-c model_reasoning_effort="ultra"` for a single genuinely hard problem, not as the default.

Keep `.codex/` committed. Codex use is mandatory (§8.6 lets experts verify it) and the
session logs are the evidence.

## Deploy — read before touching `vercel.json`

Verified working on 5 September. Two things were learned the expensive way, so they are
written down rather than rediscovered at hour four:

1. **Vercel detects the FastAPI entrypoint (`app/main.py`) natively. Do not add a rewrite.**
   A catch-all `{"source": "/(.*)", "destination": "/api/index"}` looks right and is wrong:
   it rewrites the *path itself*, so every request arrives at the app as `/api/index` and
   nothing routes. The app returns FastAPI's own 404 for every URL, which reads like a
   broken app rather than a config bug. `vercel.json` should carry function config only.

2. **`maxDuration` caps at 60s** on the free tier. An 8-step loop against a reasoning model
   can exceed that, and a judge would see a gateway timeout instead of a trail. The loop
   therefore stops itself at `DEADLINE_SECONDS = 50` and returns the partial trail with a
   visible "deadline" step. If runs get cut short on the day, lower `max_steps` or use a
   faster model — do not raise the deadline above ~55.

```bash
vercel deploy --temporary --yes   # anonymous, expires in ~1h; good for testing the pipeline
vercel login && vercel --prod     # the real thing
```

Verify a deploy in three calls, always:

```bash
curl -s -o /dev/null -w "%{http_code}" "$URL/"           # 200, HTML
curl -s "$URL/api/health"                                   # api_key_configured must be true
curl -s -X POST "$URL/api/demo" | head -c 200               # the judge's path
```

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

**Any tool that returns a list must paginate.** `agent._invoke` clips every tool result at
`TOOL_OUTPUT_LIMIT` (4000 chars), and the clip lands mid-string, so an oversized result
reaches the model as *unparseable JSON* — no error, and no way for it to ask for the rest.
Give list tools `offset`/`limit`, return a `next_offset`, cap the page server-side, and say
so in the description. Measured in rehearsal: ~20 ordinary records already overflowed.

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
