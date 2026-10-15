# Participant Rulebook — HackQuest CTF 2026

**Organized by Pragyan × IEEE-CS KLEIT Chapter · Break the Target. Own the Flag.**

---

## Format

- Fully online. Any modern browser on any device.
- Total event 4 h 30 min; competition window 3 h 45 min.
- Teams of **2–4** participants. All engineering branches welcome.
- One account per team, created by the team leader.

## Five rounds

| Round | Name | Challenges | Points each |
|---|---|--:|--:|
| 1 | Logic Labyrinth | 3 | 100 |
| 2 | Cipher Vault | 3 | 200 |
| 3 | Tech Riddles | 4 | 300 |
| 4 | Capture The Flag | 4 | 400 |
| 5 | The Debug Sprint | 1 | 500 |

Total available: **4,200 points** in tier mode (or **3,499** in normalized
mode — the active figure is always shown on the site and in the app).

### How you advance

1. Solve a challenge → you receive a **code segment**.
2. Collect every segment in the round; they concatenate into that round's
   unlock code.
3. An organizer then **opens the next round**.

Rounds never open automatically, so nobody is rushed. If a round is not open
yet you will see a waiting screen, not an error.

## Hints

Three progressive hints per challenge. **Free by default.** If a penalty is
configured, the cost is shown before you request a hint.

## Rules

1. Attack only the systems provided for HackQuest CTF. No real targets, no
   third-party or college infrastructure.
2. Do not attack the platform itself or other teams.
3. No denial-of-service or distributed denial-of-service traffic.
4. Do not share or request flags between teams.
5. Do not interfere with another team's session or environment.
6. Report infrastructure vulnerabilities to an organizer.
7. Violations may result in disqualification; organizers have final authority.

## Proctoring

The quiz runs fullscreen and reports these events to the server:

- leaving fullscreen
- switching tabs or hiding the window
- window blur (minimise or alt-tab)
- closing the page

**Three verified violations = automatic disqualification.**

### What this cannot do — please read

- A web page **cannot** see what you do in other applications, on a second
  screen, or on a phone.
- Browser events can be missed, repeated, or triggered by an innocent
  interruption such as an operating-system dialog or a notification.
- A dropped connection is **not** treated as cheating.

If a violation is recorded that you believe is wrong, contact an organizer.
Forgiveness requires a stated reason and is logged.

## Scoring and tie-breaks

1. Higher total score.
2. Earlier timestamp at which that score was reached.
3. Fewest verified violations.

All timestamps are server-side, displayed in the event timezone.

## Round 5 — submitting code

You have two options, and **your code is never executed on the competition
server**:

1. **Structured fix (recommended)** — submit JSON describing the correction,
   for example `{"comparator": 0}`. The server evaluates it against hidden
   tests using trusted code.
2. **Pasted code** — submit your corrected function. It is parsed and
   analysed for correctness but never run.

Hidden tests are not shown before the competition ends.

## After the event

Explanations for every challenge are published when each round closes. Results
are frozen, verified and then published at `/results`.

Questions? Ask an organizer in the event channel. Good luck. 🏁