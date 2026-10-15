# Organizer Guide — HackQuest CTF 2026

For the two organizer accounts. Sign in at `/login` with your organizer
username (a team account cannot reach `/admin` — that boundary is enforced
server-side).

---

## 1. Before the event

### Create both accounts

```bash
python -m app.cli bootstrap    # first organizer  -> role: admin
python -m app.cli bootstrap    # second organizer -> role: moderator
```

The first account is `admin`; subsequent ones are `moderator`.
Both are created with `must_change_password = True`, so each organizer must
change their password on first sign-in (`/profile`).

**Never share one account.** The audit log records the actor on every action,
so sharing makes disputes unresolvable.

### Roles

| Capability | admin | moderator |
|---|:--:|:--:|
| View leaderboard, teams, submissions, unlocks | yes | yes |
| Open / close / lock rounds | yes | yes |
| Review and forgive violations | yes | yes |
| Change settings (scoring, timer, event time) | yes | **no** |
| Start / pause / end the competition | yes | **no** |
| Disqualify or restore a team | yes | **no** |
| Create another organizer | yes | **no** |
| Export CSV reports | yes | yes |
| Read the audit log | yes | yes |

### Seed and verify

```bash
python -m app.cli seed           # rounds, challenges, private answer keys
python -m app.cli verify-keys    # recomputes and compares every key
```

Run `verify-keys` again after any content change. It must print
`all answer keys verified`.

---

## 2. Choose a scoring mode — read this before announcing anything

The tier weights in the brief sum to **4,200**, not 3,500:

| Round | Challenges | Points each | Subtotal |
|---|--:|--:|--:|
| 1 | 3 | 100 | 300 |
| 2 | 3 | 200 | 600 |
| 3 | 4 | 300 | 1,200 |
| 4 | 4 | 400 | 1,600 |
| 5 | 1 | 500 | 500 |
| | | | **4,200** |

Two options, set in `/admin` → Configuration → Scoring mode:

- **`tier`** — weights exactly as above. **Maximum 4,200.**
- **`normalized`** — each weight scaled by 3500/4200 and rounded half-up,
  giving 83 / 167 / 250 / 333 / 417. **Actual achievable total 3,499**
  (a documented −1 rounding delta).

The active mode and its maximum are displayed to participants on the landing
page, arena and leaderboard, and shown in the admin console. Do not mix the two
systems, and do not announce one figure while running the other.

### Hints

Default penalty is **0** (hints are free). If you set a penalty, participants
see the cost on each hint button before they use it.

---

## 3. Event-day run sheet

| When | What to do |
|---|---|
| Before 10:00 | Set the event date/time + timezone in Configuration so the countdown works |
| 10:00 | Toggle **Registration → open** |
| 10:35 | Demo the platform. Explain proctoring and the appeal process |
| 10:45 | **Start competition** (`running`), then **Open R1** |
| After each round | Let teams finish, then **Open R{n+1}**. Announce breaks |
| 2:30 | **Open R5** (Debug Sprint) |
| 2:45 | Confirm the competition timer; **Freeze board** |
| 2:55 | Verify scores against the submissions export |
| 3:05 | **Publish results**, announce winners |
| After | Close each round to publish explanations and explanations for hints |

A round being *open* does **not** force teams forward: a team only advances
when it has solved every challenge of the previous round. Set the round back to
**Lock** if you need to freeze everyone mid-round.

---

## 4. Proctoring and appeals

The server is the only authority for violations. The browser reports events; it
can never clear or reduce its own count.

Threshold: **3 verified violations → automatic disqualification.**

Typical workflow:
1. `/admin` shows the leaderboard with a violation count per team.
2. Use **Review violations** to forgive a legitimate interruption. A reason is
   **mandatory** and is written to the audit log.
3. Manual disqualification or restoration also requires a reason.
4. A reviewed violation cannot be reviewed again (HTTP 409).

### Explain these limits to participants

- A web page **cannot** detect other applications, a second monitor, a phone, or
  printed notes.
- Browser events can be missed, duplicated, or triggered by a benign OS dialog
  or notification.
- A network disconnect is **not** evidence of cheating; the heartbeat exists
  precisely to tell a drop apart from an exit.

Be transparent about this. Overstating the controls invites disputes.

---

## 5. Reports and audit

| Export | Contents |
|---|---|
| `/api/admin/export/leaderboard.csv` | Rank, team, code, solved, points, violations, status |
| `/api/admin/export/registrations.csv` | Full registration roster |
| `/api/admin/export/submissions.csv` | Every attempt with points and hint usage |

`/admin/audit` lists every organizer action with actor, target, timestamp and
IP. The table is append-only — the application exposes no update or delete
path for it.

---

## 6. Safety rails

- **Backups.** `pg_dump` before the event and after each round.
- **Passwords.** Never store them in a spreadsheet, chat, or the repository.
  Rotate with `/profile`.
- **Answer keys.** `answer_key`, `segment`, `unlock_code` and `hidden_tests`
  are never serialised to participant endpoints. There is a regression test
  asserting this (`test_answers_never_reach_the_client`) — keep it passing.
- **No live targets.** Round 4 is a self-contained fictional lab.
- **Round 5 never executes participant code.** Submitted code is parsed with
  `ast` only; evaluation happens against platform-owned functions.