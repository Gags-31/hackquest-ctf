# Organiser Manual — HACKQUEST CTF 2026

Two independent accounts have identical full access:

| Username | Role |
|---|---|
| `pragyan_lead` | Primary organiser |
| `ieee_lead` | Co-organiser |

On first login you are sent to `/change-password`. Use the temporary password issued at handover,
then set a private password of at least 10 characters. Reset either password at any time from
**Settings → Organiser accounts**; the new temporary value is shown once.

## Command centre tabs

- **overview** — totals for teams, participants, pending approvals, submissions and current round.
- **teams** — approve/reject registrations, regenerate or revoke access codes, delete teams.
- **challenges** — full bank with flags, hints, solutions and explanations. Create, edit,
  duplicate or disable challenges. This is the only place answers are visible.
- **rounds** — start / pause / resume / end each round globally. Server time is authoritative.
- **scoreboard** — private live standings with per-round columns. CSV and PDF exports at top.
- **submissions** — live flag monitor with correct/incorrect outcomes.
- **breaks** — 20 riddles, answer reveal toggle and meme templates.
- **comms** — publish announcements visible on team dashboards.
- **settings** — edit event date/time/timezone, countdown target, schedule, finalist mode,
  hint penalty, score visibility. Publish results when verification is complete.
- **audit** — every privileged action with actor and timestamp.

## Running the event

1. Approve registered teams. Only approved teams may log in.
2. Confirm the countdown target matches `2026-11-25T11:00:00+05:30`.
3. Start Round 1. All approved teams receive it simultaneously; future rounds stay locked.
4. Monitor the scoreboard and submission feed. Pause/resume applies globally.
5. End a round before starting the next one.
6. Configure final access as `all` or `shortlist` (top N by score at the moment Round 4 starts).
7. End Round 4, verify totals, then **Publish results** to expose `/results` to participants.

## Helping a stuck team

Open **challenges**, search the challenge title, and read the description, hints, solution and
concept. Never paste a flag into a participant-facing channel. Use the hint reveal controls in
**breaks** for riddles. All challenge answers are synthetic and safe to discuss.
