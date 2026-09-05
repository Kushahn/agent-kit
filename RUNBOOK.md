# RUNBOOK — 23 September 2026

Follow this. Do not improvise the schedule on the day; improvise the product.

**Venue:** МВЦ «EXPO», пр. Мәңгілік Ел 53/1, Astana. Check-in from 09:00 with your personal
QR code. You may **not leave the venue** once checked in (§3.7, §6.7).

**Assume five hours.** If it turns out longer, you gain buffer — never plan to need it.

---

## Before the gun (−0:30)

- [ ] Check in, find power and a seat near it
- [ ] Test venue Wi-Fi **and** the LAN adapter
- [ ] `uv sync` — confirm cached, no download needed
- [ ] `uv run pytest -q` — 6 green
- [ ] `vercel whoami` — still logged in
- [ ] `git config --global user.name` / `user.email` set — the organiser's repo will be
      fresh, and an unset identity blocks your first commit at hour zero (§8.6 also uses
      authorship to verify each member's contribution)
- [ ] Phone hotspot on standby, own API key in your pocket

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

## The hourly ritual (60 seconds, non-negotiable)

§6.6: a missing hour is grounds for disqualification.

```bash
git add -A
git commit -m "feat: <what actually changed this hour>"
git push
vercel --prod
```

Then one line in `PROGRESS.md`. Set a phone alarm for every hour — under pressure this is
exactly the thing that gets forgotten.

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

---

## Before you submit

- [ ] Live URL opens **in a private window** (no cached login)
- [ ] `/api/health` returns `api_key_configured: true`
- [ ] Demo button works with **zero input**
- [ ] README sections 1, 3, 6 and 7 are filled — value, how to run, potential, disclosures
- [ ] Disclosure of the pre-existing scaffold is present (§6.4)
- [ ] `.codex/` is committed — evidence of required tool use (§8.6)
- [ ] `PROGRESS.md` has a line for every hour
- [ ] Live link + any access credentials are in the submission (§8.8)
