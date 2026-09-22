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
| `app/demo_recording.json` | **Create on the day**, after the last functional change: a live demo run saved with the page's export button. With no key set, the demo button replays it, labelled as a replay. |
| `app/main.py` | FastAPI routes. Rarely changes. |
| `app/ui.py` | The page, inlined as a string constant. |
| `vercel.json` | Function config only. **Never add a catch-all rewrite** — see Deploy. |
| `tests/test_smoke.py` | Loop tests on a **throwaway registry** — they survive gutting `tools.py`. |
| `tests/test_case.py` | Write case-specific tool tests here on the day. |

## Division of labour

**Claude defines interfaces. Codex fills bodies. Claude reviews.**
Never point both at the same file at the same time.

**One conductor per person, memory in files.** You talk to Claude Code only; Claude hands
Codex a self-contained task with `codex exec` (below), reads the result and reviews the
diff before anything is committed. Do not also run a separate Codex chat on the same files:
two agents with two private memories is exactly how the work drifts apart. What both must
know lives in files they both read — this contract, `CASE.md` (the case, the one sentence,
the Not Doing list) and `PROGRESS.md` (what is done and every decision, one line each).

- A Codex task starts cold. Its prompt names the file it owns, the signature, and how to
  check it is done ("tests/test_case.py passes"). Never "as we discussed".
- Fix-ups to the task Codex just did continue its session instead of starting over:
  `codex exec -p hackathon --approve-for-me resume --last "<the fix>"`. A new task gets a new session.
- **Handoff when Claude's window runs out:** Claude's last act is a `PROGRESS.md` line saying
  what is next. Then Codex drives, starting with "Read AGENTS.md, CASE.md and PROGRESS.md
  first" — it picks up from the files, not from Claude's chat.

- **Claude** — reads the case, picks the track, writes tool *signatures and descriptions*,
  wires modules, writes the README and the pitch, keeps `PROGRESS.md` current, reviews.
- **Codex** — implements one self-contained file per task against a fixed signature.
  Owning whole files is what prevents collisions.

Delegate like this:

```bash
# Delegate. NOTE: --approve-for-me already implies the workspace-write sandbox and
# CONFLICTS with -s; passing both fails instantly with an argument error.
codex exec -p hackathon --approve-for-me -C . -o .codex/<your-name>.md "<task>"
# One output file per person: three people committing .codex/last.md conflict every hour.

# Review. -p must come BEFORE the subcommand, and a range is required.
codex exec -p hackathon review --base <commit>      # or --uncommitted
```

Run delegations in the foreground, or check the output file afterwards. A backgrounded
`codex exec` that fails on its arguments exits in under a second and the error is easy
to miss — exactly how the broken command above survived until the dress rehearsal.

`-p hackathon` loads `~/.codex/hackathon.config.toml`: reasoning effort `high`, plugins off.
**Every laptop needs that file**, or the command fails before doing anything. Do not write
it by hand — `pwsh -File bootstrap.ps1` writes it, then proves it with a live round trip and
falls back to a model-free profile if Codex rejects the pinned model.
Measured: **45s vs 2m36s** against the default `ultra` profile on a real coding task. Use
`-c model_reasoning_effort="ultra"` for a single genuinely hard problem, not as the default.

Keep `.codex/` committed. Codex is not required by the rules (§5.4.12) unless the Task's ТЗ
says so, but the session logs are part of the development history experts may check (§4.1).

## When an agent runs out — the failover drill

Claude and Codex meter independently. Either can die mid-build; the project must not. This
is why the contract lives in this file and not in one tool's memory.

**The two agents are not equally scarce on the day.** The organisers issue every participant a one-month ChatGPT & Codex Pro 5x plan at 12:30, which is roughly five times Plus - on the order of hundreds of `gpt-5.6-terra` messages per five-hour window, far more than this build can spend. Claude runs on whatever personal plan you already pay for, and nobody is topping it up. So **Codex is the workhorse and Claude is the rationed specialist**: spend Claude on the case read, the track call, tool signatures, the README and reviews, and let Codex do the volume.

**Claude has two limits and the five-hour one is the trap.** It is a *rolling window that
opens on your first message of the session*, not at midnight. A five-hour contest against a
five-hour window means that if you open Claude to "get set up" an hour before the start, it
expires an hour before the finish — during the pitch, the hour you can least afford it.

Pre-flight, the morning of:

| Check | How | What you want |
|---|---|---|
| Weekly cap headroom | `/usage` | room for a whole contest; it is separate from the 5h window |
| Session window primed | one tiny message at 09:00 sharp, then nothing until 13:00 | window A 09:00-14:00 nearly unspent; window B opens at the first message after 14:00 |
| Paid escape hatch armed | `/usage`, enable usage credits | past the cap you keep working at API rates |
| One-shot rescue held back | `/limit-reset` | clears the 5h window, once a week — do not spend it on prep |

On the day:

1. **Prime at 09:00, then leave Claude alone until 13:00.** One tiny message at 09:00 opens
   window A (09:00-14:00) almost unspent, so its whole budget goes on the case read and the
   idea gate in 13:00-14:00. The first message after 14:00 opens window B (14:00-19:00),
   which covers the finish. Cloning, `bootstrap.ps1`, reading the rules and the venue Wi-Fi
   happen in a terminal or in Codex. If window A runs dry before 14:00, Codex drives.
2. **Commit Codex output from hour one, not hour four.** `.codex/<name>.md` records who did
   what (§4.1), and if the Task's ТЗ requires a tool, it is the evidence. A person who saves
   all their Codex use for the end has nothing to show if the key or the quota dies first.
3. **Codex is a replacement driver, not a helper.** If Claude stops, nothing is blocked:

   ```bash
   # Claude's job, done by Codex. The instruction to read AGENTS.md is what carries the contract.
   codex exec -p hackathon --approve-for-me -C . -o .codex/<your-name>.md      "Read AGENTS.md first. Then: <the task Claude would have taken>"

   codex exec -p hackathon review --uncommitted    # Claude's review pass
   ```
4. **If it is the OpenAI side that dies,** the app breaks rather than the build, and §5.4.16
   drops a project that does not run — so this is the failure that actually costs the
   prize. `/api/health` will show `api_key_configured` true while every run errors in the
   trail. The organisers also issue **$50 of NVIDIA API credit** at 12:30, which is the
   only second provider you are given.

   **It is not a drop-in swap, and finding that out at hour four is the bad version.**
   NVIDIA NIM (`https://integrate.api.nvidia.com/v1`) is OpenAI-compatible on
   *chat completions*; it does not serve the **Responses** API, which is what
   `agent.py` calls. Setting `OPENAI_BASE_URL` alone will 404 every turn.

   The change is small but it is a change: one `client.chat.completions.create` branch
   that maps `tools` to the `{"type": "function", "function": {...}}` shape, reads
   `message.tool_calls` instead of `output`, and appends `{"role": "tool",
   "tool_call_id": ...}` instead of `function_call_output`. The reasoning-replay rule does
   not apply — NVIDIA's catalogue is open models (Nemotron, GLM, Kimi, Gemma), not
   reasoning models. Hand that paragraph to Codex; do not design it live.

   `PRICES` will then report 0.0, which is correct: it is not a number we can stand
   behind for another provider, and §4.1 lets experts check claimed results.
5. **Neither agent is allowed to be the only thing that knows something.** Anything decided
   in a chat gets written into `PROGRESS.md` or this file in the same hour.

## Team of three — lanes

§5.4.8 requires an hourly result from the team, and §4.1, §4.6 and §5.4.7 let the
organisers and the jury check each person's contribution. So the work splits into three lanes, each
owning whole files. One owner per file is what lets three people push to one branch
without merge conflicts.

| Lane | Owns | Typical hourly artifact |
|---|---|---|
| **Driver** | `app/tools.py`, `app/agent.py`, `app/main.py`, `vercel.json`, the deploy | tools implemented, live redeploy |
| **Data & QA** | `app/demo.py`, `tests/test_case.py` | demo data with planted cases, tests, live-URL bug list |
| **Story** | `README.md`, `app/ui.py`, slides, video | README sections, page copy, pitch |

`PROGRESS.md` is shared: everyone appends one line an hour, and `.gitattributes` unions it.

1. **Touch only files you own.** Need a change elsewhere? Ask the owner.
2. **The Driver writes the data schema first** — field names in a comment at the top of
   `app/demo.py`, inside the first 40 minutes. Data & QA fills records against it. This is
   the one interface between lanes.
3. **Only the Driver runs `vercel --prod`.** The CLI deploys the local folder, not the
   repo, so a teammate deploying from a stale checkout silently rolls the live site back.
4. **Pull before you push:** `git pull --rebase origin HEAD`. A rebase conflict means
   someone edited a file outside their lane — `git rebase --abort` and call its owner.
5. **Commit under your own name.** Authorship is how contribution gets verified.
6. **Everyone uses Codex in their own lane.** It is the abundant agent on the day, and each
   person's `.codex/<name>.md` is their contribution record. A teammate on Claude follows this same file.

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

Section numbers are from the Regulations published 22 September 2026.

1. **Something committed every hour, by everyone.** §5.4.8: a team with no confirmed
   result for any hour can be disqualified (§5.9.2). Contribution is checked per person
   (§4.1, §4.6), so each person commits under their own name and appends their own
   `PROGRESS.md` line.
2. **The README must run on a stranger's machine.** §5.4.15-5.4.16: experts install and
   launch the project from the README alone; if it does not start, the team is out and no
   fixes are accepted. Before 18:00, clone into a fresh folder and follow it word for word.
3. **Deploy at hour 0, not hour 5.** §5.6.6: key features must be testable without any
   participant's personal account, so the live URL (our key held server-side) is the demo
   access. It must stay up through expert review and Demo Day, 24-29 September.
4. **Disclose pre-existing code.** §5.4.4. This scaffold is a public template that predates
   the event. Templates are allowed only as plumbing (§5.4.4.2): the Task's main
   functionality is built during the contest. Say so in the README and the first commit.
5. **All work in the organiser's repo.** §5.4.9, §5.4.11. What it holds at 18:00 is the
   final version (§5.4.13) — push before then, and deploy no new code after it: every
   stage judges the 18:00 version (§5.4.14).
6. **Feature freeze at hour 3.** The rubric rewards a small working thing, explained well.
7. **Technical criteria come from the chosen Task's ТЗ** (§5.5), not a fixed table. Read its
   scoring table at 13:00 and build to it. Unless it scores code quality, ship ugly, ship
   working.
8. **The organisers' cybersecurity rules bind agents too.** No key, token or password in
   code, commits, README, slides or chat — keys live in `.env` and Vercel only; a leaked
   key is reported to the organisers at once, then revoked. Use only data the case provides
   or the organisers allow; keep case data marked confidential out of prompts. No network
   scans, load or DoS tests, and no working around limits — including against our own
   deployed URL on the shared network.
9. **The final README is in Russian** (the organisers' README prompt asks for it) and
   includes data and integrations and known limitations — see `README.template.md`.

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

## Case shapes, and the lazy build for each

The case is unknown until the start, so these are decided in advance rather than argued
about at hour one. In every row the point is the same: the expensive-looking option loses a
five-hour race.

| If the case gives you | Build this | Not this |
|---|---|---|
| A pile of documents to search | A `search_documents` tool scoring keyword overlap over the in-memory list, paginated | A vector database. Embeddings only repay their setup above a few thousand chunks, and you have neither the chunks nor the hour |
| Scans, photos or PDFs | Feed the image straight to the model — it is already multimodal (see below) | An OCR service, a parsing pipeline |
| Tabular records | Tools over a list of dicts, exactly as the scaffold ships | A database |
| A need to sound authoritative | Real data from data.egov.kz, disclosed | Invented records |

**Multimodal input takes one edit, on the day, only if the case needs it.** `run_agent`
sends `task` as a plain string. To send an image alongside it, pass content parts instead —
the loop needs no other change:

```python
task = [
    {"type": "input_text", "text": "Which of these site photos shows a safety breach?"},
    {"type": "input_image", "image_url": f"data:image/jpeg;base64,{b64}"},
]
```

Then in `run_agent`, `conversation` becomes `[{"role": "user", "content": task}]` with the
list passed through unchanged. Do not do this speculatively — it costs a minute when needed
and confuses the trail when it is not.

## What the trail already records

Every model turn captures its own token counts, and `to_dict()` prices the run through
`PRICES` in `app/agent.py`. The page shows it as one line above the trail:

    3 model turns · 4,812 tokens · $0.0154 per decision

That line is doing rubric work, so do not delete it when gutting files. *Потенциал развития*
is 20% of the technical score and 20% again at Demo Day, and a per-decision unit cost is the
most concrete answer there is to "could this scale". It also pre-empts the obvious hostile
question about running costs.

An unpriced model reports `0.0` rather than a guess. If you switch models on the day, either
add the two real numbers to `PRICES` or leave it at zero — never ship a plausible fake, §4.1
lets experts check claimed results.

## Real data: data.egov.kz

Real government data scores better than invented data on value and applicability, and the
case may not ship its own. Verified 10 Sept:

- **No API key needed for a snapshot.** The API (`/api/v4/...`) returns 403 without a key,
  but each dataset page's export works without one:
  `https://data.egov.kz/datasets/exportjson?index=<dataset>&version=v1&from=0&count=50`
  (`exportexcel` for a spreadsheet). The dataset id is the `index=` part of its page URL.
- **Fetch it yourself** — browser or `curl` — and hand the file to Codex to convert. Codex's
  sandbox normally has no network.
- **Snapshot into `app/demo.py`; never call the portal from the app.** It is slow and flaky
  (the first request on 10 Sept timed out at 20s), and judges test 24–28 Sept.
- **Check the update date and clean the text.** The sample pulled on 10 Sept was from 2016,
  and Kazakh letters can arrive mis-encoded (`ДОСТЫЌ` for `ДОСТЫҚ`).
- **Label planted records.** Real data has no known answers, so the demo still needs a few
  planted cases — mark them (`"synthetic": true`) and say so in the README. §4.1 lets
  experts check the reliability of claimed results.
- **Disclose it** in README §7: dataset name, URL, date fetched (§5.4.4).

## Commands

```bash
pwsh -File bootstrap.ps1                  # ONCE per laptop: Codex profile + toolchain check
uv sync                                   # install
uv run pytest -q                          # must be green before building on it
uv run uvicorn app.main:app --reload      # local, http://127.0.0.1:8000
vercel --prod                             # deploy
```

## Conventions

Python 3.12+, type hints on every signature, Google-style docstrings on public functions,
`pathlib` over `os.path`, `logging` never `print`, constants UPPER_SNAKE_CASE at module top.
Conventional commits (`feat:`, `fix:`, `chore:`, `docs:`).
