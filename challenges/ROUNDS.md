# HackQuest CTF — 5-Round Progressive Arena

Each challenge yields a **3–4 character code segment**. Segments concatenate (in order) into the next round's unlock code. Rounds stay locked until the previous one is complete. **Answers are never rendered in page source** — verified by an automated leakage audit.

## Unlock chain

| Round | Name | # | Points | Solutions |
|---|---|---|---|---|
| 1 | Logic Labyrinth | 3 | 100 ea. | `3WA` · `57X` · `1UP` → code `3WA57X1UP` |
| 2 | Cipher Vault | 3 | 200 ea. | `RUSH` · `BYTE` · `NULL` → code `RUSHBYTENULL` |
| 3 | Tech Riddles | 4 | 300 ea. | `192` · `ECHO` · `443` · `TREE` → code `192ECHO443TREE` |
| 4 | Capture The Flag | 4 | 400 ea. | `BAK` · `OR1` · `SHA` · `ROT` → code `BAKORSHAHROT` |
| 5 | Live Debugging | 1 | 500 | fixed line `total = sum(range(1, 101))` |

**Max score: 3,500**

### Round 1 — Logic Labyrinth
| # | Puzzle | Solve | Convert |
|---|---|---|---|
| 1 | Grand Sum | 1 + 2 + … + 100 = `5050` | base-36 → `3WA` |
| 2 | Sequence Ascent | F(20), F(1)=1, F(2)=1 = `6765` | base-36 → `57X` |
| 3 | Power Play | 7⁴ = `2401` | base-36 → `1UP` |

### Round 2 — Cipher Vault
| # | Cipher | Work |
|---|---|---|
| 1 | Caesar +3 | `UXVK` → `RUSH` |
| 2 | Base64 | `QllURQ==` → `BYTE` |
| 3 | ROT13 then reversed | `YYHA` → reverse → `AHYY` → ROT13 → `NULL` |

### Round 3 — Tech Riddles
`192` (digit riddle) · `ECHO` (canyon) · `443` (HTTPS port) · `TREE` (data structure)

### Round 4 — Capture The Flag
`BAK` (robots.txt extension) · `OR1` (SQL WHERE bypass) · `SHA` (hash family) · `ROT` (rotation cipher)

### Round 5 — Live Coding Debugging
Broken code multiplies instead of summing and uses `range(1, 11)`. Replace with:
```python
total = sum(range(1, 101))
```
Whitespace/dashes are stripped, so any casing works. On success → flag + winning position.

## Acceptance rules
Codes are matched case-insensitively; spaces and hyphens are ignored. Re-submitting a solved challenge is idempotent.

## Run
```bash
pip install flask gunicorn
python rounds.py          # http://localhost:5000
```
Render: build `pip install -r requirements.txt`, start `gunicorn rounds:app` (rootDir `challenges/`).

## Admin
`/admin?token=<ADMIN_TOKEN>` — standings + clear leaderboard. Token defaults to `hackquest-admin-2026`; override via `ADMIN_TOKEN` env var.