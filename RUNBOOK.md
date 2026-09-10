# RUNBOOK — 23 September 2026

Follow this. Do not improvise the schedule on the day; improvise the product.

**Venue:** МВЦ «EXPO», пр. Мәңгілік Ел 53/1, Astana. Check-in from 09:00 with your personal
QR code. You may **not leave the venue** once checked in (§3.7, §6.7).

**Assume five hours.** If it turns out longer, you gain buffer — never plan to need it.

---

## Before 19 September — every teammate

Registration and team changes close **19 Sept 23:59** (§4.7). Each person, on their own laptop:

- [ ] Registered on edu.astanahub.com, in the team, application confirmed, personal QR code
- [ ] Laptop with **5 GHz Wi-Fi** — 2.4 GHz-only laptops are refused entry (hackalem.ai) —
      plus charger and a **LAN adapter** (§4.8)
- [ ] Git with `user.name` / `user.email` set to the name you want credited
- [ ] `uv` installed; clone https://github.com/Kushahn/agent-kit, `uv sync`, `uv run pytest -q` green
- [ ] Codex installed and logged in. Create `~/.codex/hackathon.config.toml` with two lines —
      `model = "gpt-5.6-terra"` and `model_reasoning_effort = "high"` — so `-p hackathon`
      works on your laptop too (tested 10 Sept: 13s round trip). If Codex rejects the model,
      delete the first line. Then run one `codex exec -p hackathon "Reply with OK"`.
- [ ] Read `AGENTS.md` → "Team of three — lanes" and know which lane is yours

Team, once: lanes picked (whoever is more at home in Python takes Data & QA, the other
Story; coin flip if equal — swap after the rehearsal if it feels wrong), captain named (§3.5), prize split agreed **in writing** (§10.5), one team
rehearsal done (~20–21 Sept) — ideally on a Navigator or Generate-type case, the two shapes
not yet rehearsed.

---

## Before the gun (−0:30)

- [ ] Check in, find power and a seat near it
- [ ] Test venue Wi-Fi **and** the LAN adapter
- [ ] `uv sync` — confirm cached, no download needed
- [ ] `uv run pytest -q` — 7 green, on **every** laptop
- [ ] `vercel whoami` — still logged in (Driver only; nobody else deploys)
- [ ] `codex --version` — works on every laptop (Codex is mandatory)
- [ ] `git config --global user.name` / `user.email` set — the organiser's repo will be
      fresh, and an unset identity blocks your first commit at hour zero (§8.6 also uses
      authorship to verify each member's contribution)
- [ ] Phone hotspot on standby, own API key in your pocket

**Rehearsed 6 Sept.** Import + `uv sync` + tests green took **14s**; through the
disclosure commit, **under 2 minutes**. The 40 minutes budgeted for 0:00-0:40 is
thinking time, not typing — spend it on the case, not on setup.

---

## The schedule

| Window | Do | Rule |
|---|---|---|
| **0:00–0:20** | Read the cases. Pick a track with the rule below. Write the **one sentence** the demo must prove into `README.md`. | No code yet |
| **0:20–0:40** | Import the scaffold into the organiser's repo, **disclosure in the commit message**. Set `OPENAI_API_KEY` in Vercel. **Deploy — empty but live.** | Deploy before you build |
| **0:40–3:00** | Rewrite `app/tools.py` and `app/demo.py` for the case. Claude wires, Codex implements. **Commit + `PROGRESS.md` line every hour. Redeploy every hour.** | |
| **3:00** | **FEATURE FREEZE** | Non-negotiable |
| **3:00–3:45** | Make the demo case bulletproof. Open the live URL **on your phone** — that is how a judge will meet it. Record the video. | Test as a stranger |
| **3:45–4:30** | `README.template.md` → `README.md`, filled properly. Section 6 is worth 40 points across both stages. `codex review`. | Half your score |
| **4:30–5:00** | Buffer. **Submit early** — the platform will be hammered. | |

### Who does what each hour

Lanes and file ownership are in `AGENTS.md`. Every cell ends in a commit under that
person's own name — §6.6 counts each participant.

| Hour | Driver | Data & QA | Story |
|---|---|---|---|
| 0–1 | Case and track (all three, 20 min). Paste the case into `CASE.md`. Import + disclosure commit, deploy empty, write tool signatures and the data schema | Demo dataset against the schema, with planted cases the agent must catch | README §1 problem + the one-sentence claim; architecture sketch |
| 1–2 | Codex implements tool bodies; wire; redeploy | `tests/test_case.py` for the planted cases; run the demo on the live URL | Render the flags as a results table in `app/ui.py` (today they only appear inside the trail); pitch outline |
| 2–3 | Demo passes end-to-end on the live URL. **Freeze at 3:00** | Live-URL bug list; phone test; check any Kazakh output | README §5 users and §6 potential |
| 3–4 | Demo-breaking fixes only; `codex review` | Final demo data; private-window test | Video — recorded on this laptop, not the Driver's — and slides |
| 4–5 | Final deploy, **submit early** | Walk the submission checklist below | README final pass, §7 disclosures, §8 team table |

### Lane starter prompts

Codex reads `AGENTS.md` by itself, so every teammate's agent already knows the lanes. Start
from these instead of a blank prompt. Each runs as:

    codex exec -p hackathon --approve-for-me -C . -o .codex/<your-name>.md "<prompt>"

**Data & QA, 0–1** (once the Driver has pushed the schema):

    I am the Data & QA lane in AGENTS.md. Read CASE.md and the schema comment at the top of
    app/demo.py. Replace RECORDS with 30 realistic records that follow that schema, in the
    language the case uses. Plant 5 records the agent must catch and list their ids and
    reasons in a comment above RECORDS. Rewrite DEMO_TASK for this case. Edit no other file.

**Data & QA, 1–2:**

    I am the Data & QA lane in AGENTS.md. Create tests/test_case.py: for each planted record
    listed in app/demo.py, build the registry from app/tools.py, call the tools directly and
    assert they surface that record. No API key, no network. Edit no other file.

**Story, 0–1:**

    I am the Story lane in AGENTS.md. Read CASE.md and README.template.md. Replace README.md
    with the template and fill sections 1 and 2 for this case: plain sentences, for a judge
    skimming fast. Leave the other sections as the template has them. Edit no other file.

**Story, 1–2:**

    I am the Story lane in AGENTS.md. In app/ui.py, render the response's flags list as a
    table above the trail, with columns record, reason and severity; show nothing when it
    is empty. Edit no other file.

---

## Picking the track (0:00–0:20)

In priority order:

1. Can you demo one **complete narrow** scenario by hour 3? If no, drop it.
2. Does it need data or domain access you cannot get in five hours? Drop it.
3. Prefer the **less crowded** room — prizes are awarded per track (§10.1). Cybersecurity
   and Fintech draw crowds; Construction, Extractive industry and Kazakh language do not.

The ten: Kazakh language · Government services · Extractive industry · Cybersecurity ·
Healthcare · Construction · Fintech · Education · Agriculture · Creative industries.

---

## The hourly ritual (60 seconds, every person, non-negotiable)

§6.6: a missing hour for **any one participant** is grounds for disqualifying the team.
Stagger it so three pushes don't race: **Data & QA at :50, Story at :53, Driver at :56**,
and the Driver redeploys last so the live site carries everyone's work.

```bash
# first append your own line to PROGRESS.md:  | 1:50 | <you> | <what changed> | |
git add -A
git commit -m "feat: <what actually changed this hour>"
git pull --rebase origin HEAD   # teammates pushed too; PROGRESS.md merges itself (.gitattributes)
git push -u origin HEAD         # HEAD, not main: a fresh clone may sit on master
vercel --prod                   # Driver only
```

Set a phone alarm for your minute — under pressure this is exactly what gets forgotten.

---

## When it goes wrong

| Symptom | Do this |
|---|---|
| Deploy fails | You still have the last good deploy. Fix forward, do not roll back and panic. Fallback: Hugging Face Spaces. |
| Every URL 404s with `{"detail":"Not Found"}` | A rewrite in `vercel.json` is flattening the path. Remove it — Vercel routes to `app/main.py` natively. Verified 5 Sep. |
| Deployed run returns a gateway timeout | 60s function cap. The loop self-stops at 50s; if it still bites, lower `max_steps` or switch to a faster model. |
| Venue Wi-Fi dies | LAN adapter, then phone hotspot. Deps are already cached. |
| API key not provisioned | Use your own key. Never sit blocked on someone else's provisioning. |
| Claude hits its usage limit | It falls back to Sonnet automatically. If that runs out, hand the wheel to Codex — `AGENTS.md` is written so either can drive. |
| Codex is slow | You are on `-p hackathon` (effort `high`), right? Confirm the header says `reasoning effort: high`, not `ultra`. |
| Laptop RAM pressure | Close browser tabs first — the browser is the biggest consumer, not the IDE. Then Cursor. |
| Agent loops without answering | `max_steps` already caps it. Tighten the tool descriptions; vague descriptions cause thrashing. |
| `rsync: command not found` | Not in Git Bash here. Import with `git -C <src> archive HEAD \| tar -x -C .` — it also exports exactly the tracked files. |
| `rm -rf` refused by a hook | Revised 6 Sept: relative paths inside the tree are now allowed (`.venv`, `./build`). Absolute paths, `~`, `..`, `*` and unresolved variables still block by design. Use a relative path, or run it yourself. |
| Write blocked for a hidden character | Pasted text (likely from the organiser's portal) carries a soft hyphen, BOM or bidi mark. The message names the codepoint and index. Strip with `re.sub(r'[­​-‏  ‪-‮﻿]', '', text)` and rewrite. |
| `src refspec main does not match any` | You are on `master`. Push `HEAD`, not a branch name. |
| `CONFLICT` during `git pull --rebase` | Someone edited a file outside their lane. `git rebase --abort`; the file's owner decides which version wins. `PROGRESS.md` never conflicts — it is union-merged. |
| Live site suddenly shows old behaviour | Someone other than the Driver ran `vercel --prod` from a stale checkout. Driver pulls and redeploys. |
| A teammate's laptop can't see the venue Wi-Fi | 2.4 GHz-only card. LAN adapter first — this is why it is on the checklist. |
| Agent ignores most of a long list | A list tool overflowed `TOOL_OUTPUT_LIMIT` and arrived as broken JSON. Paginate it — see `AGENTS.md`. |

---

## Before you submit

- [ ] Live URL opens **in a private window** (no cached login)
- [ ] `/api/health` returns `api_key_configured: true`
- [ ] Demo button works with **zero input**
- [ ] README sections 1, 3, 6 and 7 are filled — value, how to run, potential, disclosures
- [ ] Disclosure of the pre-existing scaffold is present (§6.4)
- [ ] `.codex/` is committed — evidence of required tool use (§8.6)
- [ ] `PROGRESS.md` has a line for every hour **from every person**
- [ ] Live link + any access credentials are in the submission (§8.8)
