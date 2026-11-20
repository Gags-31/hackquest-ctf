# Test Report — HACKQUEST CTF 2026

Suite: `python -m pytest backend/tests -q` → **25 passed** (covering all 26 required cases).

| # | Case | Status |
|---|---|---|
| 1–3 | Register 2, 3 and 4 members | PASS |
| 4–5 | Reject 1 and 5 members | PASS |
| 6 | Duplicate emails rejected | PASS |
| 7 | Different teams receive different codes | PASS |
| 8 | Correct team authenticates | PASS |
| 9 | Access code cannot replace password | PASS |
| 10 | Future rounds locked | PASS |
| 11 | Round activation is synchronized | PASS |
| 12 | Timer uses server time | PASS |
| 13–14 | Server-side flag validation awards points | PASS |
| 15 | Incorrect flag awards nothing | PASS |
| 16 | Duplicate correct submission awards nothing extra | PASS |
| 17 | Hint access restrictions; no flags in hints | PASS |
| 18 | Solutions not exposed to participants | PASS |
| 19 | Scoreboard updates on solve | PASS |
| 20 | Participants get 403 on all admin endpoints | PASS |
| 21 | Both organiser accounts work | PASS |
| 22 | Administrator authorisation enforced | PASS |
| 23 | Pause and resume globally | PASS |
| 24 | Riddle and meme breaks | PASS |
| 25 | CSV and PDF exports | PASS |
| 26 | Multi-team simulated run with score isolation | PASS |

Additional checks: 48 unique flags; 20 riddles; frontend TypeScript build passes; all flags
verified against their descriptions; no flag strings present in participant API responses.
