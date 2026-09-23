<!--
FILL THIS IN ON THE DAY. Copy over README.md and delete these comments.

"This event" below means the table at the top of AGENTS.md. An AI judge may read this
before any human does. Write plainly, claim only what the repo can back, and put the
numbers where a skimmer will find them.

TREAT IT AS A HARD GATE: judges often install and launch the project from the README
alone, and a project that does not start may be out with no fixes accepted. It covers:
  purpose ................ sections 1-2     architecture ........... section 4
  technologies ........... section 4       install / start-up ..... section 3
  dependencies ........... section 3       environment variables .. section 3
  system requirements .... section 3       checking the main scenario ... section 3
Before the code freeze, clone the repo into a fresh folder and follow section 3 word for word.

At kickoff, copy the rubric's criteria here and make sure each one has a section a skimmer
can find. If the organisers publish their own README list or prompt, follow it and add
whatever it asks for that is missing below.

WRITE IT IN THE LANGUAGE THE ORGANISERS ASK FOR (This event). Claim only what the repo
confirms. No keys, tokens or passwords anywhere in it.
-->

# <PROJECT NAME>

**Case / track:** <the one case or track this is entered for>
**Team:** <name> — <members>
**Live demo:** <URL>  ·  **Health check:** <URL>/api/health  ·  no account or API key needed

> One sentence: what this does and for whom.

## 1. The problem

Who has this problem, how often, and what it costs them today. Be specific to the case —
use the case document's own words for the required result. Two short paragraphs.

## 2. What we built

Three to five bullets. What the thing actually does, not what it aspires to.

- …
- …

## 3. Run it

The judge will not have your data or your accounts. The demo button must work on the
deployed URL with no input at all.

**Fastest path — no account needed:** open <URL> and press **Run the demo case**. The API
key is held on the server, so this is the demo access for the model API.

**No key at all?** Run it locally anyway: with `OPENAI_API_KEY` unset, the demo button
replays a recorded real run of the demo case (`app/demo_recording.json`), labelled as a
replay. Set the key for a live run.

### System requirements

- Windows, macOS or Linux; Python **3.12+**
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Internet access, and an OpenAI-compatible API key for local runs

### Dependencies

FastAPI, uvicorn (the `standard` extra, which provides `--env-file`), Pydantic, the OpenAI
Python SDK — declared in `pyproject.toml`, locked in `uv.lock`. pytest for the tests.

### Environment variables

| Variable | Required | Default | What it does |
|---|---|---|---|
| `OPENAI_API_KEY` | for live runs | — | Key for the model API; unset, the demo replays |
| `MODEL` | no | `<model>` | Model name |
| `LLM_PROTOCOL` | no | `responses` | `chat` for a chat-completions provider |
| `OPENAI_BASE_URL` | no | OpenAI (NVIDIA NIM when `LLM_PROTOCOL=chat`) | Another OpenAI-compatible endpoint |

### Install and start

```bash
uv sync                       # or: pip install -r requirements.txt "uvicorn[standard]" pytest
cp .env.example .env          # then put your key in OPENAI_API_KEY
uv run pytest -q              # <N> tests, no API key needed
uv run uvicorn app.main:app --env-file .env   # or: uvicorn app.main:app --env-file .env
# open http://127.0.0.1:8000 — without --env-file the key is not loaded
```

### Check the main scenario

1. Open the page and press **Run the demo case**.
2. **You should see:** the agent inspects the data with its tools, flags <N> records with
   stated reasons, and prints a summary. Every model turn and tool call appears in the trail
   below the answer, and exports as JSON.
3. `GET /api/health` returns `"api_key_configured": true` when the key is set, and
   `"demo_recording": true` when a replay ships.

## 4. How it works

```
input data ──▶ agent loop (OpenAI Responses API, tool calling)
                   │  every turn and tool call recorded
                   ▼
             audit trail ──▶ decision + JSON export
```

- `app/agent.py` — the loop; caps steps so a runaway cannot burn the token budget
- `app/tools.py` — the tools the model can call; registry built per request
- `app/main.py` — FastAPI; `app/ui.py` — the page
- **Technologies:** Python 3.12, FastAPI, OpenAI <model> with tool calling, plain HTML/JS.
- Deployed on Vercel. No database: the trail travels in the response, which is one less
  thing to break.

Tool failures are returned to the model as text rather than raised, so a bad call is
recovered from instead of ending the run.

## 5. Who would use this

Name the actual operator — an agency, a department, a team — and the decision it replaces
or speeds up. What it would plug into. No business model required by the rubric; just make
the use concrete.

## 5a. Data and integrations

Every data source (provided by the case, public, or synthetic — say which), and every
external API or service the app calls, with what it is used for.

## 6. Where it goes next

**Most rubrics score growth or scaling potential, often heavily — check its weight in This
event.** Write it properly.

- **Next month:** …
- **At scale:** what changes when it handles 10,000 records instead of 8
- **Adjacent uses:** other tracks or organisations the same machinery serves
- **What it would take:** the honest list of what is missing for production

## 6a. Known limitations

What this version does not do, and where it can be wrong. Honest and specific: a judge who
finds a limitation you did not list trusts the rest less.

- …

## 7. Disclosures

Most events require these; match the organisers' wording if they give one (This event).

- **Pre-existing code:** built on `agent-kit`, our own public template created before the
  hackathon (https://github.com/Kushahn/agent-kit, MIT, public since 6 September 2026 — its
  commit history predates <event start date> and is externally timestamped). It contains
  only plumbing — the agent loop, FastAPI wiring, the page, and deploy config. The main
  functionality for the case (tools, prompts, data handling, UI copy) was written during
  the contest, <build window>.
- **Libraries:** FastAPI, Pydantic, the OpenAI Python SDK, uvicorn.
- **Models:** OpenAI <model> via the Responses API.
- **AI development tools:** Codex and Claude Code. Codex session logs are
  committed under `.codex/`.
- **Datasets:** <source, or "synthetic, generated for the demo">.

## 8. Team

| Name | Role | Contribution |
|---|---|---|
| … | captain | … |

*(Judges may verify each participant's actual contribution — keep this honest and make sure
the git history matches it.)*
