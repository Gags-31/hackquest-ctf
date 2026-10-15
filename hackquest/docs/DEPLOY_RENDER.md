# Deploying HackQuest CTF 2026 to Render

The new platform lives in `hackquest/`. Deploy it as a **separate service** so
the existing Flask arena keeps working.

## Why a new service

The current `hackquest-ctf.onrender.com` already serves the legacy Flask app.
Redeploying it in place risks taking the live event links offline — which is
exactly what happened during a first attempt, when the service began returning
500s on every route because a dependency install failed in the build.

## Option A — Blueprint (recommended)

1. Push this repo (done).
2. Render → **New** → **Blueprint**
3. Select `Gags-31/hackquest-ctf`
4. Render finds `render.yaml` by default — instead choose **Add from file** and
   pick `render-hackquest.yaml`.
5. Set the required secret when prompted:
   ```
   SECRET_KEY = <python -c "import secrets;print(secrets.token_urlsafe(48))">
   ```
6. Deploy.

Your URL becomes `https://hackquest-2026.onrender.com`.

The service:
- installs only `hackquest/backend/requirements.txt`
- serves the API and, from the repository, the pre-built SPA in
  `hackquest/frontend/dist`
- persists the SQLite database on a 1 GB disk so scores survive restarts

## Option B — Manual web service

| Setting | Value |
|---|---|
| Root directory | `hackquest/backend` |
| Runtime | Python 3.12 |
| Build command | `pip install -r requirements.txt` |
| Start command | `gunicorn app.main:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 60` |
| Health check path | `/api/health` |

Environment variables:

```
ENVIRONMENT=production
DATABASE_URL=sqlite:///./hackquest.db
SECRET_KEY=<random 48+ chars>
PROCTOR_VIOLATION_LIMIT=3
HINT_PENALTY=0
```

## After the first deploy

The app **auto-seeds** on an empty database, so rounds and challenges exist
immediately. Create your two organizer accounts — this cannot be done over
HTTP on a fresh deploy, so open a shell (Render → your service → Shell) or run
it locally against the same database:

```bash
python -m app.cli bootstrap   # admin
python -m app.cli bootstrap   # moderator
python -m app.cli verify-keys # expect 15/15
```

## If the service returns 500

Check the **build** log first — a 500 on every route usually means
`pip install` failed and gunicorn cannot import the app. Read the log; the
working Pin versions are pinned in `hackquest/backend/requirements.txt`.

Other causes:

| Symptom | Cause | Fix |
|---|---|---|
| 500 on all routes | dependency install failed | read the build log |
| `/` shows JSON, not the site | `frontend/dist` missing | commit `hackquest/frontend/dist` (`npm run build` in `hackquest/frontend`) |
| Scores vanish on restart | no disk mounted | add a Render disk, or set `DATABASE_URL` to Postgres |
| `SECRET_KEY` warning in logs | default in use | set a real one |

## PostgreSQL instead of SQLite

```bash
# Render -> New -> Postgres, then set on the web service:
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname
```

## Local check before deploying

```bash
cd hackquest/backend
python -m pytest -q                 # 77 tests
python -m app.cli verify-keys       # 15/15
cd ../frontend && npm run build     # regenerates dist
```