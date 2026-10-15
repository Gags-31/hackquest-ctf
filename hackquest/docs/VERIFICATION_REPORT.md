# HackQuest CTF 2026 — Verification Report

**Generated:** 2026-10-15
**Scope:** what was actually executed and confirmed, and what was not.

This report deliberately distinguishes **verified by execution** from
**written but unexecuted**. Nothing below is claimed to work unless it was run.

---

## 1. Environment

| Component | Version |
|---|---|
| Python | 3.12 (Windows) |
| FastAPI | 0.115.6 |
| SQLAlchemy | 2.0.36 |
| argon2-cffi | 23.1.0 |
| Node | 22.x |
| Vite | 5.4.21 |
| TypeScript | 5.7.x |
| Tailwind | 3.4.x |
| Database (tests) | SQLite (file) |
| Database (prod) | PostgreSQL 16 — **not exercised locally** |

---

## 2. Automated tests — VERIFIED

```
77 passed
```

Run with `cd backend && python -m pytest -q`.

| Area | File | Coverage |
|---|---|---|
| Answer keys, hints, unlock assembly | `test_answer_keys.py` (27 tests) | Every one of the 15 keys; decoys; base-36/Base64/cipher maths; unlock-code concatenation order; scoring arithmetic |
| Registration → results flow | `test_competition.py` (33 tests) | Team-size limits, duplicates, auth, CSRF, role isolation, round gating, submissions, hints, unlock codes, scoring modes, freeze/publish, exports, audit |
| Integrity, proctoring, leakage | `test_integrity.py` (17 tests) | Rate limits, server-authoritative violations, DQ immutability, appeals, reconnection, answer-key leakage sweep |

### Real bugs these tests caught (all fixed)

1. **CSRF cookie never set.** `/api/auth/csrf` constructed a `Response` object
   that FastAPI discarded, so the cookie was never written and *every*
   state-changing request failed. Would have broken the real application.
2. **`Query.scalar_one()` does not exist** in SQLAlchemy 2.0 — a 500 error on
   every round view and submission.
3. **Base64 validator destroyed its input.** `norm_upper_strip()` uppercased the
   submission, but Base64 is case-sensitive; the correct answer was rejected.
4. **Binary challenge required binary input.** The brief says "Validator:
   Integer answer", but the validator demanded a 6-character binary string, so
   a team answering `45` was marked wrong.
5. **Unlock codes were empty.** Seed assembled them before challenges were
   flushed and before stale relationship caches were cleared.
6. **Comparator extraction missed `n % 2`** — a `BinOp`, not a `Name` — so
   correct pasted Round 5 code was never recognised.
7. **`verify-keys` CLI was wrong.** It fed stored answer keys to validators, but
   for base-36/Base64 rounds the participant's submission differs from the key.
   Added `SAMPLE_SUBMISSIONS` and fixed the CLI.

---

## 3. Challenge content — VERIFIED

`python -m app.cli verify-keys` → **`15/15 challenges verified`**

| Round | # | Challenge | Accepted submission | Segment |
|---|--:|---|---|---|
| 1 | 1 | Arithmetic Accumulator | `276` (2850 in base 36) | `276` |
| 1 | 2 | Fibonacci Signal | `40` (144 in base 36) | `40` |
| 1 | 3 | Exponent Engine | `1UP` (2401 in base 36) | `1UP` |
| 2 | 4 | Caesar Lock | `HACK` (KDFN − 3) | `HACK` |
| 2 | 5 | Encoded Transmission | `SGFja1F1ZXN0` | `HackQuest` |
| 2 | 6 | Reversed Signal | `BAF` (reverse + ROT13) | `SNO` |
| 3 | 7 | The Missing Number | `48` | `48` |
| 3 | 8 | The Memory Keeper | `STACK` | `STACK` |
| 3 | 9 | Port Detective | `443` | `443` |
| 3 | 10 | Binary Whisper | `101101` or `45` | `45` |
| 4 | 11 | Hidden Configuration | `/training/blue-door` | `/training/blue-door` |
| 4 | 12 | Login Logic | `trainee:demo-pass` | `trainee:demo-pass` |
| 4 | 13 | Hash Hunter | `SHA-256` | `SHA-256` |
| 4 | 14 | Rotation Station | `CAESAR` | `CAESAR` |
| 5 | 15 | Broken Counter | `{"comparator": 0}` or correct code | `count_evens-fixed` |

Assembled unlock codes:

| Round | Code |
|---|---|
| 1 | `276401UP` |
| 2 | `HACKHackQuestSNO` |
| 3 | `48STACK44345` |
| 4 | `/training/blue-doortrainee:demo-passSHA-256CAESAR` |
| 5 | `count_evens-fixed` |

Round 5 hidden tests: 5 published + 5 secret, all passing against the correct
predicate; the broken odd-check fails them.

---

## 4. Scoring — VERIFIED

The brief's correction is confirmed. Tier weights total **4,200**, not 3,500.

| Round | × Points | Subtotal |
|---|--:|--:|
| 1 (3) | 100 | 300 |
| 2 (3) | 200 | 600 |
| 3 (4) | 300 | 1,200 |
| 4 (4) | 400 | 1,600 |
| 5 (1) | 500 | 500 |
| | | **4,200** |

| Mode | Weights | Max |
|---|---|--:|
| `tier` | 100/200/300/400/500 | **4,200** |
| `normalized` | 83/167/250/333/417 | **3,499** |

Rounding policy (documented, not silent): each tier scaled by 3500/4200 and
rounded half-up; the achievable total is 3,499, a −1 delta against the nominal
3,500 ceiling. Both figures are surfaced in the API, the admin console, the
landing page, the arena and the leaderboard.

---

## 5. Frontend — VERIFIED

```
npx tsc --noEmit      → clean, 0 errors
npx vite build        → built in 18.60s
   dist/index.html                 0.60 kB
   dist/assets/index-*.css        19.66 kB  (gzip  4.13 kB)
   dist/assets/index-*.js        218.30 kB  (gzip 66.58 kB)
```

12 routes implemented: landing, rules/FAQ, register, login, dashboard, arena,
round, unlock/waiting, leaderboard, profile, admin, audit, results, 404.

TypeScript `strict` with `noUnusedLocals`/`noUnusedParameters` is enabled.

---

## 6. Full-stack integration — VERIFIED

**Live HTTP run against uvicorn: `24 passed, 0 failed`.**

A scripted client registered a team, solved all 15 challenges across five
rounds and was scored, with organizer actions driven over the same API.

| Check | Result |
|---|---|
| Organizer login, settings read | pass |
| Scoring max reported as 4,200 | pass |
| Start competition, open rounds 1–5 | pass |
| Team registration | pass |
| Round 1 unlocked for a new team | pass |
| No `unlock_code` in any participant response | pass |
| Rounds 1–4 solved → 3,700 points | pass |
| Unlock codes issued on round completion | pass |
| Duplicate submission not re-scored | pass |
| Dangerous Round 5 code rejected (422) | pass |
| Round 5 structured patch accepted, +500 | pass |
| Leaderboard shows team at full 4,200 | pass |
| Audit log populated | pass |
| CSV export contains the team | pass |
| End competition | pass |

Also verified directly:

- `GET /api/health` → `{"ok":true,"app":"HackQuest CTF 2026"}`
- Backend serves the built SPA at `/` with the correct `<title>`
- `python -m app.cli bootstrap` creates an admin and refuses duplicates

Three genuine behaviours were confirmed during this run and are worth calling
out, because each initially looked like a failure:

1. **Duplicate registration returns 409** even when the name matches an
   existing team — the guard works.
2. **Re-submitting an already-solved challenge short-circuits** before the
   sandbox runs, returning `already_accepted` and never re-awarding points.
3. **A full clean run totals 4,200**, the tier maximum, matching the corrected
   arithmetic exactly.

### Still not verified

| Item | Status |
|---|---|
| PostgreSQL | **Not run.** All tests used SQLite. The code supports both, but `psycopg2` paths are unexercised locally. |
| Docker build / `docker compose up` | **Not run.** Docker is not installed on this machine. |
| Email verification | **Not functional by design.** With no SMTP configured, teams are auto-verified and recovery returns a generic message without sending mail. Stated in the admin console and `SECURITY.md`. |
| Real code-execution sandbox | **Not implemented, by design.** No container sandbox. Round 5 uses AST analysis plus a structured patch evaluated by platform-owned code. `CONTAINER_SANDBOX_CMD` is unset. |
| Browser manual QA, screen readers, mobile | **Not performed.** No human browser walkthrough was run. |
| Load / performance testing | **Not performed.** |

---

## 7. Security controls — implemented, and their honest limits

**Implemented:** Argon2id hashing; signed `HttpOnly`/`SameSite`/`Secure`
sessions rotated after password change; dual-identity cookies so team and
organizer sessions cannot be confused; server-side authorization on every
protected route; CSRF double-submit with constant-time comparison; CSP and
hardening headers; parameterised SQL throughout; rate limits on login,
registration, submissions, unlocks and hints; append-only audit log;
unique constraint preventing double-scoring; non-root container; duplicate
registration blocked.

**Answer secrecy — regression-tested.** `test_answers_never_reach_the_client`
sweeps `/api/rounds`, all five round endpoints and `/api/leaderboard` for
unlock codes, `answer_key`, `hidden_tests`, `unlock_code` and post-round
explanation text. Passes.

**Round 5 never executes participant code.** `test_r5_never_executes_code`
parses `sandbox.py` with `ast` and fails if `eval`, `exec`, `compile` or
`__import__` is ever called. Passes. Dangerous constructs (`import`, `while`,
`open`, dunder attributes) are rejected with a 422.

**Proctoring limits are documented, not overstated.** See
`docs/SECURITY.md`: a page cannot detect other applications, second monitors
or phones; browser events can be false-positived by benign OS interruptions;
the server is the sole authority and a team cannot reverse its own
disqualification.

---

## 8. What must happen before the event

1. `cd backend && python -m pytest -q` — must stay green.
2. `python -m app.cli verify-keys` — must print `15/15`.
3. Stand up the real stack: `docker compose up --build`, then repeat the
   registration→results walkthrough **in a browser**.
4. Test once against PostgreSQL, not SQLite.
5. Generate a real `SECRET_KEY` and database password; confirm `.env` is
   untracked.
6. Create **both** organizer accounts; complete first-login password changes.
7. Set a custom event date/timezone so the countdown works.
8. Decide and announce the scoring mode; never announce 3,500 while running
   tier mode.
9. Decide `PROCTOR_VIOLATION_LIMIT` and brief participants on the honest
   limitations.
10. Back up PostgreSQL before the event and after each round.