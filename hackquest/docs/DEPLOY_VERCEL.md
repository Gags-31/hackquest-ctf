# HackQuest CTF 2026 on Vercel

The platform is served by a single Python serverless function at `api/index.py`.
Mangum adapts the FastAPI ASGI app, and the same function serves the compiled
React SPA from `frontend/dist`.

## Layout

| File | Purpose |
|---|---|
| `vercel.json` | routes every path to the Python function, 60s timeout |
| `api/index.py` | initialises the DB, seeds rounds/challenges, exposes `handler` |
| `requirements.txt` | Vercel-specific Python dependencies (includes `mangum`) |

## Environment variables (Production)

| Name | Value |
|---|---|
| `SECRET_KEY` | long random string (`python -c "import secrets;print(secrets.token_urlsafe(48))"`) |
| `DATABASE_URL` | `sqlite:////tmp/hackquest.db` |
| `ENVIRONMENT` | `production` |

## Important limitation

Vercel's serverless filesystem is read-only except `/tmp`, and `/tmp` is **not
shared between function instances**. With the SQLite default, registrations,
scores and organizer accounts are therefore ephemeral — they can disappear on a
cold start.

For a real event, attach a PostgreSQL database and set `DATABASE_URL` to its
connection string, then add `psycopg2-binary` to `requirements.txt`. All other
behaviour is unchanged.

## Redeploy

```bash
vercel --prod --yes
```

## Refreshing hints on an existing database

Hint text is stored in the database, not read from `seed.py` at request time.
After changing hints, run:

```bash
cd backend
python -m app.cli refresh-hints
```

This only updates `initial_clue`, `hint1`, `hint2` and `hint3`. Answer keys,
segments, unlock codes, scores, round state and submissions are untouched, so
it is safe to run on a live event database. `python -m app.cli seed` also calls
the same refresh automatically.
