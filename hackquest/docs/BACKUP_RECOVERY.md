# Backup & Recovery

## What to back up

| Item | Why | Method |
|---|---|---|
| PostgreSQL database | Teams, scores, unlocks, violations, audit log | `pg_dump` |
| `.env` | Secrets — back up separately, never in git | password manager |
| Organizer credentials | Event access | password manager |

## Create a backup

```bash
# From the host running PostgreSQL
docker compose exec -T db pg_dump -U hackquest -d hackquest -Fc > hackquest-$(date +%F-%H%M).dump
```

Verify the dump is not empty before relying on it:

```bash
ls -lh hackquest-*.dump
docker compose exec -T db pg_restore --list < hackquest-*.dump | head
```

**Restore test.** An untested backup is not a backup. Once, before the event:

```bash
docker compose exec -T db createdb -U hackquest hackquest_restore
cat hackquest-*.dump | docker compose exec -T db pg_restore -U hackquest -d hackquest_restore
docker compose exec -T db psql -U hackquest -d hackquest_restore -c "select count(*) from teams;"
```

## Restore

```bash
docker compose stop app
docker compose exec -T db dropdb -U hackquest hackquest
docker compose exec -T db createdb -U hackquest hackquest
cat hackquest-<timestamp>.dump | docker compose exec -T db pg_restore -U hackquest -d hackquest
docker compose start app
curl -fsS https://your-host/api/health
```

## Recovering mid-event

The database is the only stateful component; the frontend is static and the
API is stateless. Worst realistic cases:

| Situation | Action |
|---|---|
| App container restarted | Nothing to do — state lives in PostgreSQL |
| Postgres restarted | Docker restarts it via `restart: unless-stopped` |
| Postgres volume corrupted | Restore the latest dump; replay announcements manually |
| `SECRET_KEY` rotated by accident | Everyone is signed out; teams re-login with the same credentials |
| Frontend served stale JS | Browser hard-reload; assets are content-hashed |

## What is deliberately not persisted

- Sessions are signed cookies, not server-side rows. Restoring an old database
  does not invalidate sessions, but rotating `SECRET_KEY` does.
- Rate-limit counters are in-process. A restart clears them.

## After the event

Keep the final dump and all three CSV exports together, archived with the
results announcement. Verify once more that the dump restores cleanly.