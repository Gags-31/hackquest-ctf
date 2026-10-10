# Security Guidelines

## Authentication
Hash passwords with PBKDF2-HMAC-SHA256 (or bcrypt/argon2) with per-user salt.
Issue short-lived signed JWTs (HS256 minimum). Include sub, role and exp claims.
Verify signature and expiry on every protected request.

## Authorization
Enforce role-based access control server-side on every mutating endpoint.
Ownership checks: users may only modify resources they own unless they hold an
admin role. Never rely on the frontend hiding buttons.

## Input Validation
Validate every request body and query parameter with typed schemas. Reject
unknown fields where practical. Constrain lengths, ranges and formats.

## Injection and XSS
Use ORM parameter binding only - never string-format SQL. Render user content
as text in the frontend; never inject it via dangerouslySetInnerHTML.

## Secrets and Configuration
Load secrets from environment variables. Reject hardcoded credentials.
Restrict CORS to known origins instead of "*".

## Rate Limiting and Transport
Rate-limit authentication endpoints to slow brute-force attacks. Serve over
HTTPS in production. Keep dependencies updated and scan for known CVEs.

## Security Review Checklist
weak authentication, authorization gaps, hardcoded secrets, unsafe endpoints,
SQL injection, cross-site scripting, insecure configuration, vulnerable
dependencies, improper input validation, missing rate limiting.
