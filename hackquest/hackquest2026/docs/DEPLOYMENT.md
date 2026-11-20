# Deployment — HACKQUEST CTF 2026

## Vercel

The repository is deployed from this directory as a single Python function.

1. `vercel link` from `hackquest2026/` and choose the project.
2. Set environment variables:
   - `SECRET_KEY` — long random value
   - `DATABASE_URL` — for a real event, a persistent PostgreSQL URL
   - `ENVIRONMENT=production`
   - `ORG1_PASSWORD`, `ORG2_PASSWORD` — temporary organiser passwords
3. `vercel --prod`

`api/index.py` exposes `app` for Vercel's Python runtime and normalises any function-prefixed
paths so FastAPI routes stay intact. `vercel.json` rewrites all routes to the function.

### Persistence warning

The default `DATABASE_URL` is `sqlite:////tmp/hackquest.db`. That works for demos but is
ephemeral on Vercel. For live event data, attach PostgreSQL and add `psycopg[binary]` to
`requirements.txt`. Then redeploy; seeding is idempotent and will not overwrite existing teams
or submissions.

## Docker / local server

```powershell
python -m pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
python backend/cli.py seed
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
```

## Database

`python backend/cli.py seed` creates all tables and loads:

- 4 rounds with durations 50 / 60 / 60 / 45 minutes
- 48 challenges with unique `HQCTF{...}` flags, 2 hints, solutions and concepts
- 20 riddles across four breaks, 6 meme templates
- event date, schedule, marquee, scoring and hint settings

It is safe to re-run; challenge hints, flags and settings are refreshed, while teams,
submissions and scores are preserved.
