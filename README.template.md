<!--
FILL THIS IN ON THE DAY. Copy over README.md and delete these comments.

The section order deliberately mirrors the stage-1 scoring table (Положение §7.4), because
an AI judge reads this before any human does (§8.3-8.4). Write plainly, claim only what the
repo can back, and put the numbers where a skimmer will find them.

  Problem & value ............ 15   <- section 1
  Prototype functionality .... 25   <- section 3 (must be verifiable FROM THE REPO)
  Technical implementation ... 15   <- section 4
  Practical applicability .... 15   <- section 5
  Development potential ...... 20   <- section 6  (highest-value section; also 20 more at Demo Day)
  README & reproducibility ... 10   <- sections 2-3
-->

# <PROJECT NAME>

**Track:** <one of the ten>
**Team:** <name> — <members>
**Live demo:** <URL>  ·  **Health check:** <URL>/api/health

> One sentence: what this does and for whom.

## 1. The problem

Who has this problem, how often, and what it costs them today. Be specific to the track —
the rubric checks that the solution matches the track you entered. Two short paragraphs.

## 2. What we built

Three to five bullets. What the thing actually does, not what it aspires to.

- …
- …

## 3. Run it in two minutes

The judge will not have your data. The demo button must work on the deployed URL with no
input at all.

**Fastest path:** open <URL> and press **Run the demo case**.

**From this repo:**

```bash
uv sync
cp .env.example .env          # add OPENAI_API_KEY
uv run pytest -q              # 7 tests, no API key needed
uv run uvicorn app.main:app --reload
# open http://127.0.0.1:8000 and press "Run the demo case"
```

**What you should see:** the agent inspects the data with its tools, flags <N> records with
stated reasons, and prints a summary. Every model turn and tool call appears in the trail
below the answer, and exports as JSON.

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
- Deployed on Vercel. No database: the trail travels in the response, which is one less
  thing to break.

Tool failures are returned to the model as text rather than raised, so a bad call is
recovered from instead of ending the run.

## 5. Who would use this

Name the actual operator — an agency, a department, a team — and the decision it replaces
or speeds up. What it would plug into. No business model required by the rubric; just make
the use concrete.

## 6. Where it goes next

**The highest-scoring section: 20 points here and 20 more at Demo Day.** Write it properly.

- **Next month:** …
- **At scale:** what changes when it handles 10,000 records instead of 8
- **Adjacent uses:** other tracks or organisations the same machinery serves
- **What it would take:** the honest list of what is missing for production

## 7. Disclosures

Required by Положение §6.4.

- **Pre-existing code:** built on `agent-kit`, our own public boilerplate created before the
  hackathon (https://github.com/Kushahn/agent-kit, public since 6 September — commit
  history predates 23 September and is externally timestamped). It contains only plumbing —
  the agent loop, FastAPI wiring, the page, and deploy config. All case-specific work
  (tools, prompts, data handling, UI copy) was written during the contest.
- **Libraries:** FastAPI, Pydantic, the OpenAI Python SDK, uvicorn.
- **Models:** OpenAI <model> via the Responses API.
- **AI development tools:** Codex (required) and Claude Code. Codex session logs are
  committed under `.codex/`.
- **Datasets:** <source, or "synthetic, generated for the demo">.

## 8. Team

| Name | Role | Contribution |
|---|---|---|
| … | captain | … |

*(§8.6 lets the organisers verify each participant's actual contribution — keep this honest
and make sure the git history matches it.)*
