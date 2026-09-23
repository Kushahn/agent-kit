# AGENTS.md — the contract

Single source of truth for both agents. `CLAUDE.md` points here. Written so **either
Claude or Codex can drive this project alone**, because one of them may hit a usage
limit mid-build.

## What this project is

Ingest unknown data → a tool-calling agent reasons over it → an **auditable decision**.
The audit trail is the product, not a debug aid: a hackathon that judges *agentic*
solutions wants evidence that the thing reasons, and a visible chain of tool calls is that
evidence. An AI judge may read it first.

## This event — fill in at kickoff

Everything in this file holds at any hackathon. What changes from one event to the next
lives in this table and nowhere else; the rest of the file points here as "This event".
Fill it from the organisers' rules before the build starts (if the captain has a local
`EVENT.md` brief, copy the facts from it). Leave a row as `unknown` rather than guess, and
ask the captain when an unknown row blocks a decision.

| Fact | This event |
|---|---|
| Event, format (on-site / remote / hybrid) | |
| Build window (start – end, local time) | |
| Code freeze: the version that gets judged | |
| Checkpoint rule (e.g. a committed result every hour) | |
| Judging window: the live URL must stay up until | |
| Rubric: criteria and weights | |
| Required tools or platforms | |
| Credits handed out (which agent or model, when) | |
| Repository: ours or the organisers' | |
| Disclosure of pre-existing code | |
| README language and required sections | |
| Data rules (confidential data, allowed sources) | |

**Times derived from the build window.** Feature freeze at about 60% of it (hour 3 of 5,
hour 14 of 24). Data schema written within the first ~15% (40 minutes of 5 hours). The
README clone test (Rules, 2) before the code freeze, with time left to fix what it finds.

## Layout

| Path | Role |
|---|---|
| `app/agent.py` | The loop. Model turns, tool dispatch, trail capture. Rarely changes. |
| `app/tools.py` | **Gut this on the day.** Tools are the case-specific part. |
| `app/demo.py` | **Gut this on the day.** The bundled case the demo button runs. |
| `app/demo_recording.json` | **Create on the day**, after the last functional change: a live demo run saved with the page's export button. With no key set, the demo button replays it, labelled as a replay. |
| `app/chat_compat.py` | Lets the same loop run on a chat-completions provider. See the failover drill. |
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

Keep `.codex/` committed. The session logs are development history judges may check, and
if the event requires an AI tool (This event), they are the evidence.

## When an agent runs out — the failover drill

Claude and Codex meter independently. Either can die mid-build; the project must not. This
is why the contract lives in this file and not in one tool's memory.

**The two agents are rarely equally scarce.** Check This event for credits the organisers
hand out. Whichever agent has the bigger quota that day is the workhorse; the other is the
rationed specialist. When the event issues ChatGPT & Codex credit and Claude runs on a
personal plan nobody is topping up, spend Claude on the case read, the track call, tool
signatures, the README and reviews, and let Codex do the volume.

**Claude has two limits, and in a short contest the five-hour one is the trap.** It is a
*rolling window that opens on your first message of the session*, not at midnight. Open
Claude to "get set up" an hour before a five-hour contest and the window expires an hour
before the finish — during the pitch, the hour you can least afford it. In a 24-hour or
longer event the window resets several times over, and the weekly cap is the limit to watch.

Pre-flight, the morning of:

| Check | How | What you want |
|---|---|---|
| Weekly cap headroom | `/usage` | room for the whole build window; it is separate from the 5h window |
| Session window primed (contests under ~10h) | one tiny message 4 hours before the start, then nothing until the start | window A nearly unspent for the first hour; window B opens at the first message after A ends |
| Paid escape hatch armed | `/usage`, enable usage credits | past the cap you keep working at API rates |
| One-shot rescue held back | `/limit-reset` | clears the 5h window, once a week — do not spend it on prep |

On the day:

1. **Prime 4 hours before the start, then leave Claude alone until the start.** For a start
   at 13:00: one tiny message at 09:00 opens window A (09:00-14:00) almost unspent, so its
   whole budget goes on the case read and the idea gate in the first hour. The first
   message after 14:00 opens window B (14:00-19:00), which covers a five-hour finish.
   Cloning, `bootstrap.ps1`, reading the rules and the venue Wi-Fi happen in a terminal or
   in Codex. If window A runs dry early, Codex drives.
2. **Commit Codex output from hour one, not the last hour.** `.codex/<name>.md` records who
   did what, and if the event requires an AI tool it is the evidence. A person who saves
   all their Codex use for the end has nothing to show if the key or the quota dies first.
3. **Codex is a replacement driver, not a helper.** If Claude stops, nothing is blocked:

   ```bash
   # Claude's job, done by Codex. The instruction to read AGENTS.md is what carries the contract.
   codex exec -p hackathon --approve-for-me -C . -o .codex/<your-name>.md      "Read AGENTS.md first. Then: <the task Claude would have taken>"

   codex exec -p hackathon review --uncommitted    # Claude's review pass
   ```
4. **If it is the OpenAI side that dies,** the app breaks rather than the build, and a
   project that does not run is usually dropped — so this is the failure that actually
   costs the prize. `/api/health` will show `api_key_configured` true while every run
   errors in the trail.

   **The switch is configuration, not code.** Second providers (NVIDIA NIM,
   `https://integrate.api.nvidia.com/v1`, is the common one handed out as credit) speak
   *chat completions*, not the **Responses** API that `agent.py` calls, so setting
   `OPENAI_BASE_URL` alone would 404 every turn. `app/chat_compat.py` bridges that. Set, in
   `.env` locally and in the Vercel project settings:

   | Variable | Value |
   |---|---|
   | `LLM_PROTOCOL` | `chat` |
   | `OPENAI_API_KEY` | the other provider's key |
   | `MODEL` | a model id from that provider's catalogue |
   | `OPENAI_BASE_URL` | only if the provider is not NVIDIA NIM (NIM is the default under `chat`) |

   Then redeploy (`vercel --prod`): Vercel applies changed variables only to new
   deployments. Check `/api/health` shows `"protocol": "chat"` and run the demo once.

   `PRICES` will then report 0.0, which is correct: it is not a number we can stand behind
   for another provider, and judges may check claimed results.
5. **Neither agent is allowed to be the only thing that knows something.** Anything decided
   in a chat gets written into `PROGRESS.md` or this file in the same hour.

## Team lanes

Many events check each person's contribution, and some require a result at every checkpoint
(This event). So the work splits into lanes, each owning whole files. One owner per file is
what lets several people push to one branch without merge conflicts. The table is built for
three; with two, the Driver also takes Data & QA; with four, split Story into the README and
pitch on one side and the page and video on the other.

| Lane | Owns | Typical checkpoint artifact |
|---|---|---|
| **Driver** | `app/tools.py`, `app/agent.py`, `app/main.py`, `vercel.json`, the deploy | tools implemented, live redeploy |
| **Data & QA** | `app/demo.py`, `tests/test_case.py` | demo data with planted cases, tests, live-URL bug list |
| **Story** | `README.md`, `app/ui.py`, slides, video | README sections, page copy, pitch |

`PROGRESS.md` is shared: everyone appends one line per checkpoint, and `.gitattributes`
unions it.

1. **Touch only files you own.** Need a change elsewhere? Ask the owner.
2. **The Driver writes the data schema first** — field names in a comment at the top of
   `app/demo.py`, early (see the derived times under This event). Data & QA fills records
   against it. This is the one interface between lanes.
3. **Only the Driver runs `vercel --prod`.** The CLI deploys the local folder, not the
   repo, so a teammate deploying from a stale checkout silently rolls the live site back.
4. **Pull before you push:** `git pull --rebase origin HEAD`. A rebase conflict means
   someone edited a file outside their lane — `git rebase --abort` and call its owner.
5. **Commit under your own name.** Authorship is how contribution gets verified.
6. **Everyone uses the workhorse agent in their own lane** — usually Codex (see the
   failover drill). Each person's `.codex/<name>.md` is their contribution record. A
   teammate on Claude follows this same file.

## Deploy — read before touching `vercel.json`

Verified working on 5 September 2026. Two things were learned the expensive way, so they
are written down rather than rediscovered mid-build:

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

## Rules that hold at almost every hackathon

Check each against This event; where the organisers' rules are stricter, theirs win.

1. **Something committed every checkpoint, by everyone.** Some events disqualify a team
   with no result for a checkpoint, and many check contribution per person, so each person
   commits under their own name and appends their own `PROGRESS.md` line.
2. **The README must run on a stranger's machine.** Judges often install and launch the
   project from the README alone, and a project that does not start may be out with no
   fixes accepted. Before the code freeze, clone into a fresh folder and follow it word
   for word.
3. **Deploy at hour 0, not in the last hour.** Judges test without any participant's
   personal account, so the live URL (our key held server-side) is the demo access. It
   must stay up until the judging window closes (This event).
4. **Disclose pre-existing code.** This scaffold is a public template that predates any
   event it is used at. Where templates are allowed, it is usually only as plumbing: the
   case's main functionality is built during the contest. Say so in the README and the
   first commit.
5. **All work in the repo the organisers name.** What it holds at the code freeze is
   usually the version every stage judges — push before then, and deploy no new code after
   it.
6. **Feature freeze at about 60% of the build window.** Rubrics reward a small working
   thing, explained well.
7. **Build to the rubric.** Copy its criteria and weights into This event at kickoff and
   make sure each one has something a judge can find. Unless it scores code quality, ship
   ugly, ship working.
8. **Security rules bind agents too.** No key, token or password in code, commits, README,
   slides or chat — keys live in `.env` and Vercel only; a leaked key is reported to the
   organisers at once, then revoked. Use only data the case provides or the organisers
   allow; keep case data marked confidential out of prompts. No network scans, load or DoS
   tests, and no working around limits — including against our own deployed URL on a
   shared network.
9. **The README follows the organisers' language and required sections** (This event).
   `README.template.md` covers the usual list, including data and integrations and known
   limitations.

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

The case is usually unknown until the start, so these are decided in advance rather than
argued about in the first hour. In every row the point is the same: the expensive-looking
option loses a timed race.

| If the case gives you | Build this | Not this |
|---|---|---|
| A pile of documents to search | A `search_documents` tool scoring keyword overlap over the in-memory list, paginated | A vector database. Embeddings only repay their setup above a few thousand chunks, and you have neither the chunks nor the hour |
| Scans, photos or PDFs | Feed the image straight to the model — it is already multimodal (see below) | An OCR service, a parsing pipeline |
| Tabular records | Tools over a list of dicts, exactly as the scaffold ships | A database |
| A need to sound authoritative | Real public data, snapshotted and disclosed (see Real public data) | Invented records |

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

That line is doing rubric work, so do not delete it when gutting files. Most rubrics score
growth or scaling potential, often heavily, and a per-decision unit cost is the most
concrete answer there is to "could this scale". It also pre-empts the obvious hostile
question about running costs.

An unpriced model reports `0.0` rather than a guess. If you switch models on the day, either
add the two real numbers to `PRICES` or leave it at zero — never ship a plausible fake;
judges may check claimed results.

## Real public data

Real data scores better than invented data on value and applicability, and the case may not
ship its own. Most countries run an open-data portal; the rules below hold for any of them.

- **Fetch it yourself** — browser or `curl` — and hand the file to Codex to convert. Codex's
  sandbox normally has no network.
- **Snapshot into `app/demo.py`; never call the portal from the app.** Portals are slow and
  flaky, and judges test for days after the event.
- **Check the update date and clean the text.** Old snapshots and mis-encoded letters are
  common.
- **Label planted records.** Real data has no known answers, so the demo still needs a few
  planted cases — mark them (`"synthetic": true`) and say so in the README. Judges may check
  the reliability of claimed results.
- **Disclose it** in the README's Disclosures section: dataset name, URL, date fetched.

**Worked example — Kazakhstan, data.egov.kz** (verified 10 September 2026):

- **No API key needed for a snapshot.** The API (`/api/v4/...`) returns 403 without a key,
  but each dataset page's export works without one:
  `https://data.egov.kz/datasets/exportjson?index=<dataset>&version=v1&from=0&count=50`
  (`exportexcel` for a spreadsheet). The dataset id is the `index=` part of its page URL.
- The first request timed out at 20s; the sample pulled was from 2016; Kazakh letters
  arrived mis-encoded (`ДОСТЫЌ` for `ДОСТЫҚ`).

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
