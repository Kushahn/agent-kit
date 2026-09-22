<!--
FILL THIS IN ON THE DAY. Copy over README.md and delete these comments.

Section numbers are from the Regulations published 22 September 2026. An AI judge may read
this before any human does (§4.2-4.3). Write plainly, claim only what the repo can back,
and put the numbers where a skimmer will find them.

HARD GATE (§5.4.15-5.4.16): experts install and launch the project from this README alone.
If it does not start, the team is out and no fixes are accepted. It must contain all of:
  purpose ................ sections 1-2     architecture ........... section 4
  technologies ........... section 4       install / start-up ..... section 3
  dependencies ........... section 3       environment variables .. section 3
  system requirements .... section 3       checking the main scenario ... section 3
Before 18:00, clone the repo into a fresh folder and follow section 3 word for word.

Technical scoring comes from the chosen Task's ТЗ (§5.5), not a fixed table. At 13:00,
copy its criteria here and make sure each one has a section a skimmer can find.
-->

# <PROJECT NAME>

**Task:** <the one Task this is entered for>
**Team:** <name> — <members>
**Live demo:** <URL>  ·  **Health check:** <URL>/api/health  ·  no account or API key needed

> One sentence: what this does and for whom.

## 1. The problem

Who has this problem, how often, and what it costs them today. Be specific to the Task —
use the ТЗ's own words for the required result. Two short paragraphs.

## 2. What we built

Three to five bullets. What the thing actually does, not what it aspires to.

- …
- …

## 3. Run it

The judge will not have your data or your accounts. The demo button must work on the
deployed URL with no input at all.

**Fastest path — no account needed:** open <URL> and press **Run the demo case**. The API
key is held on the server, so this is the demo access for the model API.

### System requirements

- Windows, macOS or Linux; Python **3.12+**
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Internet access, and an OpenAI-compatible API key for local runs

### Dependencies

FastAPI, uvicorn, Pydantic, the OpenAI Python SDK, python-dotenv — pinned in
`pyproject.toml` and `uv.lock` (`requirements.txt` for pip). pytest for the tests.

### Environment variables

| Variable | Required | Default | What it does |
|---|---|---|---|
| `OPENAI_API_KEY` | yes, for the agent | — | Key for the model API |
| `MODEL` | no | `<model>` | Model name |
| `LLM_PROTOCOL` | no | `responses` | `chat` for a chat-completions provider |
| `OPENAI_BASE_URL` | no | OpenAI | Another OpenAI-compatible endpoint |

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
3. `GET /api/health` returns `"api_key_configured": true` when the key is set.

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

## 6. Where it goes next

**Worth 20 points at Demo Day (§5.7.2), and check whether the Task's ТЗ scores it too.**
Write it properly.

- **Next month:** …
- **At scale:** what changes when it handles 10,000 records instead of 8
- **Adjacent uses:** other tracks or organisations the same machinery serves
- **What it would take:** the honest list of what is missing for production

## 7. Disclosures

Required by Regulations §5.4.4.

- **Pre-existing code:** built on `agent-kit`, our own public template created before the
  hackathon (https://github.com/Kushahn/agent-kit, MIT, public since 6 September — commit
  history predates 23 September and is externally timestamped). It contains only plumbing —
  the agent loop, FastAPI wiring, the page, and deploy config — which §5.4.4.2 allows. The
  main functionality for the Task (tools, prompts, data handling, UI copy) was written
  during the contest, 13:00-18:00.
- **Libraries:** FastAPI, Pydantic, the OpenAI Python SDK, uvicorn.
- **Models:** OpenAI <model> via the Responses API.
- **AI development tools:** Codex and Claude Code. Codex session logs are
  committed under `.codex/`.
- **Datasets:** <source, or "synthetic, generated for the demo">.

## 8. Team

| Name | Role | Contribution |
|---|---|---|
| … | captain | … |

*(§4.1 and §4.6 let the experts and the jury verify each participant's actual contribution — keep this honest
and make sure the git history matches it.)*
