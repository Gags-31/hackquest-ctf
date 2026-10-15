# Event-Day Operations Checklist — HackQuest CTF 2026

Print this. Tick as you go.

## Before the day (T-1)

- [ ] `SECRET_KEY` regenerated (48+ random bytes), stored in `.env`, `.env` untracked by git
- [ ] PostgreSQL password set and stored in a secret manager or `.env`
- [ ] `docker compose up --build` succeeds; `/api/health` returns `ok`
- [ ] `python -m app.cli verify-keys` → `15/15 challenges verified`
- [ ] `python -m pytest -q` → all pass
- [ ] Both organizer accounts created (`python -m app.cli bootstrap` twice)
- [ ] Both organizers have signed in once and changed their password
- [ ] Scored a practice run end-to-end in a browser
- [ ] Event date + timezone set in Admin → Configuration (so the countdown works)
- [ ] **Scoring mode decided and agreed:** `tier` (4,200) or `normalized` (3,499)
- [ ] `PROCTOR_VIOLATION_LIMIT` decided (default 3)
- [ ] Hint penalty decided (default 0 = free)
- [ ] Backup scheduled: `pg_dump`
- [ ] Participant rulebook circulated; proctoring limits explained honestly

## 09:30 — Setup

- [ ] Server up, `/api/health` green
- [ ] Dashboard live and reachable by a phone
- [ ] Backup taken pre-event
- [ ] Moderator briefing: proctoring review procedure, appeals, what to escalate

## 10:00 — Registration

- [ ] Admin → Configuration → **Registration: open**
- [ ] Verify teams as they arrive (Admin → Teams → verify)
- [ ] Confirm each team can log in and reach the Arena
- [ ] Watch for duplicate-name / duplicate-email rejections
- [ ] Registration closes when the welcome begins

## 10:20 — Welcome

- [ ] Explain the five rounds and how unlock codes work
- [ ] **Explain proctoring AND its limits** — other apps, second screens and phones are out of scope; false positives happen; appeals exist
- [ ] Confirm the threshold and that the server is the authority
- [ ] Explain hints and whether they cost points

## 10:35 — Demo

- [ ] Walk through one challenge live
- [ ] Show the leaderboard and the score-displayed-maximum
- [ ] Show where results/explanations appear afterwards

## 10:45 — Start

- [ ] Admin → **Start competition** (`running`)
- [ ] Admin → **Open R1**
- [ ] Confirm teams see "Round 1 open"
- [ ] Post an announcement: "Round 1 is live"

## During each round

- [ ] Monitor `/api/health` and server logs
- [ ] Watch the leaderboard for stuck teams
- [ ] Review violations as they arrive — **forgive genuine interruptions**, reason required
- [ ] Answer technical questions in the event channel
- [ ] At round end: confirm most teams finished, then **Open R{n+1}**
- [ ] Announce breaks via the announcement box
- [ ] Backup between rounds if time allows

## 14:30 — Final Round

- [ ] **Open R5** (Debug Sprint)
- [ ] Remind teams: hidden tests run server-side; structured fix is the safe path
- [ ] Be ready for clarification on the required tests

## 14:45 — Close

- [ ] Confirm the competition timer has elapsed
- [ ] Admin → **Freeze board**
- [ ] Export submissions CSV
- [ ] Spot-check: top teams' scores against their submission rows

## 14:55 — Verify

- [ ] Investigate any anomaly (duplicate submissions, missing unlocks)
- [ ] Resolve provisional disqualifications
- [ ] Freeze a screenshot of the final board

## 15:05 — Announce

- [ ] Admin → **Publish results**
- [ ] Announce winners and special mentions
- [ ] Confirm `/results` is public and correct
- [ ] Distribute certificates

## After

- [ ] Close each round to publish explanations
- [ ] `pg_dump` final backup
- [ ] Export all three CSVs and archive them
- [ ] Note technical issues and lessons learned
- [ ] Remove `.env` from any shared location; rotate secrets if shared
- [ ] Draft the post-event report and publish highlights