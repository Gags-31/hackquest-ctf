# HackQuest CTF 2026

**Pragyan × IEEE-CS KLEIT Chapter**
*Break the Target. Own the Flag.*

A complete, production-oriented online capture-the-flag platform: five
progressive rounds, 15 challenges, organizer-controlled release, team
scoring, live leaderboard, proctoring with an appeal process, and an
append-only audit log.

---

## Quick start

```bash
# Backend
cd backend
pip install -r dev-requirements.txt
export SECRET_KEY=$(python -c "import secrets;print(secrets.token_urlsafe(48))")
export DATABASE_URL=sqlite:///./hackquest.db
python -m app.cli seed            # 5 rounds, 15 challenges, private keys
python -m app.cli verify-keys     # must print 15/15
python -m app.cli bootstrap       # first organizer (admin)
uvicorn app.main:app --reload

# Frontend (second terminal)
cd frontend
npm install
npm run dev                      # http://localhost:5173
```

Docker:

```bash
cp .env.example .env             # set SECRET_KEY and POSTGRES_PASSWORD
docker compose up --build
```

Full instructions: [`README.md`](README.md)

---

## The five rounds

| Round | Name | Challenges | Points each | Unlock code |
|---|---|--:|--:|---|
| 1 | Logic Labyrinth | 3 | 100 | `276401UP` |
| 2 | Cipher Vault | 3 | 200 | `HACKHackQuestSNO` |
| 3 | Tech Riddles | 4 | 300 | `48STACK44345` |
| 4 | Capture The Flag | 4 | 400 | `/training/blue-doortrainee:demo-passSHA-256CAESAR` |
| 5 | The Debug Sprint | 1 | 500 | `count_evens-fixed` |

Unlock codes are **generated server-side** and never sent to participants.

### Scoring

Tier weights total **4,200**, not 3,500:

- `tier` mode — 100/200/300/400/500, **max 4,200**
- `normalized` mode — 83/167/250/333/417 (scaled by 3500/4200, rounded half-up), **max 3,499**

The active mode and its maximum are displayed throughout the app. Choose in
Admin → Configuration and do not announce one figure while running the other.

---

## Architecture

```
Frontend   React 18 + TypeScript (strict) + Tailwind + Vite
Backend    FastAPI + SQLAlchemy 2.0 + Argon2id
Database   PostgreSQL 16 (SQLite for local development)
Auth       Signed HttpOnly session cookies, CSRF double-submit, RBAC
Deploy     Docker + Docker Compose
Tests      pytest (backend), vitest configured (frontend)
```

```
backend/
  app/
    main.py        FastAPI app, middleware, security headers
    config.py      environment-driven settings
    db.py          engine + session
    models.py      ORM models
    security.py    Argon2id, sessions, CSRF
    validators.py  server-side answer validation
    sandbox.py     Round 5 — AST analysis, never executes code
    scoring.py     scoring modes, tie-breaks, CSV
    audit.py       append-only audit log
    seed.py        15 challenges + private keys
    cli.py         bootstrap / seed / verify / reset
    routers/       auth, rounds, public, admin
  tests/           77 tests
frontend/
  src/
    lib/           api client, types, proctoring hook
    pages/         12 routed pages
docs/
  ORGANIZER_GUIDE.md        roles, run sheet, scoring, appeals
  PARTICIPANT_RULEBOOK.md   what participants are told
  EVENT_DAY_CHECKLIST.md    printable day-of checklist
  SECURITY.md              controls, limits, residual risk
  BACKUP_RECOVERY.md        pg_dump, restore, mid-event recovery
  VERIFICATION_REPORT.md    what was actually tested
```

---

## Security posture

- Argon2id password hashing; session token rotated after password change
- Server-side authorization on every protected route (never frontend guards)
- CSRF double-submit with constant-time comparison
- Parameterised SQL throughout; answer keys never serialised to participants
- Rate limits on login, registration, submissions, unlocks, hints
- Append-only audit log with actor, target, timestamp and IP
- **Round 5 never executes participant code** — AST analysis plus a structured
  patch evaluated by platform-owned functions
- **Proctoring uses browser-standard signals only.** A web page cannot damage a
  participant's computer, and this platform does not attempt it. The server is
  the sole authority for violations.

Read [`docs/SECURITY.md`](docs/SECURITY.md) before claiming the app is
"secure". It is defensible, not perfect.

---

## Verification status

| Check | Result |
|---|---|
| Backend test suite | **77 passed** |
| Answer key verification | **15/15** |
| Live end-to-end HTTP run | **24/24 passed** |
| TypeScript strict typecheck | clean |
| Production frontend build | 66.6 kB gzipped |
| PostgreSQL | not run locally |
| Docker build | not run locally |
| Email verification | not configured — see SECURITY.md |
| Browser manual QA | not performed |

Full detail, including every bug the tests caught:
[`docs/VERIFICATION_REPORT.md`](docs/VERIFICATION_REPORT.md)

---

## Documentation

| Document | Audience |
|---|---|
| [`README.md`](README.md) | Install, run, deploy |
| [`docs/ORGANIZER_GUIDE.md`](docs/ORGANIZER_GUIDE.md) | The two organizers |
| [`docs/PARTICIPANT_RULEBOOK.md`](docs/PARTICIPANT_RULEBOOK.md) | Participants |
| [`docs/EVENT_DAY_CHECKLIST.md`](docs/EVENT_DAY_CHECKLIST.md) | Anyone on event day |
| [`docs/SECURITY.md`](docs/SECURITY.md) | Security review |
| [`docs/BACKUP_RECOVERY.md`](docs/BACKUP_RECOVERY.md) | Whoever holds the pager |
| [`docs/VERIFICATION_REPORT.md`](docs/VERIFICATION_REPORT.md) | Honest test status |