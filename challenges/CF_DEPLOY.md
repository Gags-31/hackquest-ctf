# Deploying HackQuest CTF to Cloudflare

Your Flask app runs **unchanged** inside a Cloudflare Container. No code changes.

## How it works
```
Browser → Cloudflare Worker (hackquest-ctf.<subdomain>.workers.dev)
        → Container (your exact Flask app + SQLite)
```

## Prerequisites
- A Cloudflare account
- The **Workers Paid** plan ($5/month) — Containers require it

## Deploy

### 1. Log in
```bash
npx wrangler login
```

### 2. Edit your secrets
Open `wrangler.jsonc` and replace the placeholders:
```jsonc
"SECRET_KEY": "<paste a long random string>",
"ADMIN_TOKEN": "<your organiser token>"
```
Generate one with:
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 3. Choose a subdomain
`npx wrangler subdomain hackquest` — this sets the URL you get after deploy.

### 4. Deploy
```bash
npx wrangler deploy
```

Your URL will look like:
```
https://hackquest-ctf.<your-subdomain>.workers.dev
```

### 5. Add a custom domain (no provider name at all)
In the Cloudflare dashboard → Workers & Pages → your worker → Settings → Domains & Routes → Add a custom domain. Point a CNAME at the `workers.dev` address and Cloudflare provisions SSL automatically.

---

## Alternative: build the image in GitHub Actions

If you'd rather not install Docker locally, `.github/workflows/build-ctf-image.yml` builds and pushes to GHCR on every push to `challenges/**`. Then in `wrangler.jsonc`, replace the `image` block:

```jsonc
"image": "ghcr.io/Gags-31/hackquest-ctf:latest"
```

Set the package to **public** (or add `CF_DOCKER_REGISTRY` credentials) so Cloudflare can pull it.

---

## Verify the migration
- Arena: `https://<your-url>/`
- Organiser panel: `https://<your-url>/organiser`
- Leaderboard: `https://<your-url>/leaderboard`

Scoring, rounds, gating, sessions and the final-round grader are byte-for-byte identical to the Render deployment.

## Notes
- SQLite persists inside the container instance but **resets if the instance restarts**. For durable data, keep using Render's instance or point `DATABASE_URL` at a Postgres (the app already supports it via `psycopg2`).
- Keep **one instance** (`"instances": 1`) — multiple instances would each get their own SQLite file and split the leaderboard.