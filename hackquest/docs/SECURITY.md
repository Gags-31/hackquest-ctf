# Security, Proctoring & Residual Risk

## Honest statement

This application is **not claimed to be perfectly secure**. It is a
competition platform built with standard, defensible controls. What follows
documents what is enforced, what is deliberately not attempted, and the risks
that remain.

---

## 1. Proctoring — what is and is not possible

### What the server enforces

| Event | Detected via | Recorded |
|---|---|---|
| Tab hidden / switched | `visibilitychange` | yes |
| Window blur (minimise, alt-tab) | `blur` | yes |
| Fullscreen exited | `fullscreenchange` | yes |
| Page closed | `beforeunload` | yes |

- The **server** counts violations. The browser can only *report* an event; it
  cannot set, lower, or clear a count. There is no endpoint a team can use to
  reverse its own disqualification.
- Counters are unique per team and server-timestamped.
- Three verified violations set the team status to `disqualified`.
- Organizer forgiveness **requires a reason** and writes an audit entry. A
  reviewed violation cannot be reviewed twice.

### What is deliberately not attempted, and why

**A web page cannot damage a participant's computer.** There is no browser API
to shut down, reboot, or alter an operating system. Any site claiming to do so
is either lying or attempting to install malware. This platform does neither,
and no participant code, script, or binary is ever delivered to a participant's
machine.

### Known residual risk — please brief participants truthfully

1. **Out of scope entirely:** other applications, a second monitor, a phone in
   hand, printed notes, a second browser profile.
2. **False positives are possible.** A legitimate OS dialog, notification,
   screen-lock, or a browser DevTools refresh can all raise `blur` or
   `visibilitychange`.
3. **Events can be lost.** A crash or force-quit may skip `beforeunload`.
4. **`beforeunload` is unreliable** on mobile, where browsers reclaim tabs
   aggressively.
5. **Fullscreen is a request, not a lock.** A determined participant can exit
   it — the exit *is* the signal being detected.
6. **A heartbeat exists precisely so a network drop is not mistaken for
   cheating.** Disconnects are not counted as violations.

Overstating these controls produces unfair disqualifications. State the limits
openly; run an appeal process; be prepared to forgive.

---

## 2. Code execution (Round 5)

**No participant code is ever executed by the API process.** There is no
`eval`, no `exec`, no `restricted`, and no shell invocation anywhere in the
submission path. A regression test (`test_r5_never_executes_code`) parses
`sandbox.py` with `ast` and fails if any call to `eval`, `exec`, `compile` or
`__import__` appears.

Two safe paths exist:

1. **Structured patch** — the participant declares the fix as JSON
   (`{"comparator": 0}`). The platform then evaluates it with its own trusted
   predicate against hidden tests.
2. **Pasted code** — parsed with `ast` and statically analysed. `import`,
   `global`, `while`, `eval`, `exec`, `open`, dunder attribute access and
   similar constructs are rejected with an explanatory error.

`ast.literal_eval` is used and is safe: it parses literals and cannot execute
arbitrary code.

### If you later want real execution

Put the runner in a **separate, disposable container** with no network, a
read-only filesystem, seccomp, a memory cap, a CPU quota, an output cap, and a
hard wall-clock timeout (gVisor or Firecracker). Do not enable it inside the
API process. `CONTAINER_SANDBOX_CMD` is intentionally **unset** in this
deployment.

---

## 3. Controls implemented

**Authentication & sessions**
- Argon2id password hashing (configurable time/memory cost).
- Constant-time credential comparison; a hash is run even for unknown users to
  reduce timing signal.
- Server-side signed session cookies: `HttpOnly`, `SameSite=Lax`, `Secure` in
  production.
- Session token **rotated after a password change** (session-fixation defence).
- Dual cookie authentication: organizer identity and team identity cannot be
  confused or cross-used.
- Forced password change on first sign-in for organizers.
- Account enumeration avoided on both login failure and password recovery.

**Authorization**
- Every protected route resolves the actor server-side from the cookie.
- `require_team`, `require_organizer` and `require_admin` are enforced in the
  dependency layer, never by a frontend route guard.
- Moderators are blocked from settings, competition control, and disqualification.

**CSRF**
- Double-submit cookie. The cookie is readable by JS, echoed in
  `X-CSRF-Token`, compared with `hmac.compare_digest`.
- A **real bug was caught here in testing**: the `/api/auth/csrf` handler built
  a `Response` that FastAPI discarded, so the cookie was never set. Fixed.

**Input & output**
- All SQL goes through SQLAlchemy parameters — no string-built queries.
- Pydantic validation with explicit length bounds.
- Answer keys, segments, unlock codes and hidden tests are **never serialised**
  into participant endpoints. Covered by `test_answers_never_reach_the_client`.
- Errors return generic messages so internals and keys are never echoed.

**Rate limiting** — login (10 / 5 min), registration (8 / hour), submissions
(30 / min), unlocks (20 / 5 min), hints (20 / 5 min).

**Other**
- CSP, `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy`.
- CORS only when origins are explicitly configured.
- Append-only audit log for every organizer action, with actor and IP.
- Duplicate submissions blocked by a unique constraint — points cannot be
  awarded twice.
- Container image runs as a non-root user with a health check.

---

## 4. Residual risks

| Risk | Severity | Mitigation |
|---|---|---|
| The in-memory rate limiter is per-process; with multiple workers the effective limit multiplies. | Low | Put a real limiter (nginx, Redis) in front for a large event |
| Sessions are stateless signed cookies: a stolen cookie is valid until expiry | Medium | `Secure`, `HttpOnly`, `SameSite=Lax`, short `SESSION_MAX_AGE` |
| No 2FA on organizer accounts | Medium | Restrict admin routes by network/VPN; add TOTP if budget allows |
| Audit log is append-only by convention, not by database constraint | Medium | Add a DB trigger denying `UPDATE`/`DELETE` |
| Recovery flow is a stub — it records the request but sends no mail without SMTP | Low | Configure SMTP, or distribute resets through organizers |
| Proctoring false positives | **Medium–High** | Published limits, documented appeal, forgiving by default |
| No WAF or DDoS protection in front | Medium | Cloudflare or equivalent in front of the app |
| Challenge content is stored in the same DB as credentials | Low | Separate DBs/roles in a hardened deployment |

---

## 5. Pre-event security checklist

- [ ] `SECRET_KEY` regenerated, 48+ random bytes, never committed
- [ ] `POSTGRES_PASSWORD` unique, stored in a secret manager or `.env` only
- [ ] Both organizer accounts created; first-login password change completed
- [ ] Bootstrap endpoint verified as **closed** once an organizer exists
- [ ] Registration open only when you intend it
- [ ] `python -m app.cli verify-keys` passes
- [ ] `pytest -q` passes, including `test_answers_never_reach_the_client`
- [ ] HTTPS enforced; `ENVIRONMENT=production` so cookies get `Secure`
- [ ] `ALLOWED_ORIGINS` set if the SPA is on a different origin
- [ ] PostgreSQL backups scheduled and a restore rehearsed
- [ ] Cloudflare or a rate limiter in front of the app
- [ ] Proctoring limits and the appeal process explained to participants
- [ ] CSV exports verified after a mock run
- [ ] `.env` confirmed absent from git

---

## 6. Responsible disclosure

Report any issue privately to the organizing committee rather than
exploiting it. This is a student event; findings will be credited and fixed
promptly.