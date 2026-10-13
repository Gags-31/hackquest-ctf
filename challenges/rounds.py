"""HackQuest CTF - 5-Round Progressive Challenge Arena
Round 1 Puzzles -> Round 2 Ciphers -> Round 3 Tech Riddles -> Round 4 CTF -> Round 5 Live Debug
Each solved puzzle reveals a code segment. Segments concatenate into the next round's unlock code.
Answers are never shown in page source. Progress is stored per team.
Run: python rounds.py -> http://localhost:5000
"""
import os
import sqlite3
import base64
import codecs
import string
import hashlib
from flask import Flask, request, render_template_string, session, make_response, redirect

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "hackquest_ctf_secret")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "hackquest-admin-2026")
DB = os.path.join(os.path.dirname(__file__), "ctf.db")
DATABASE_URL = os.environ.get("DATABASE_URL", "")
IS_PG = DATABASE_URL.startswith("postgres")
PORT = os.environ.get("PORT", "5000")

# ============================ ANSWER DATA (SERVER SIDE ONLY) ============================
# Round 1 - Logic puzzles. Answer is base36 of the numeric solution.
R1 = [
    {"id": "r1p1", "seg": "3WA", "num": 5050,
     "title": "The Grand Sum",
     "desc": "Add every integer from 1 to 100 inclusive. Then convert the total to base-36 (uppercase, no leading zeros).",
     "example": "For example, 255 decimal becomes 73 in base-36."},
    {"id": "r1p2", "seg": "57X", "num": 6765,
     "title": "Sequence Ascent",
     "desc": "The sequence is F(1)=1, F(2)=1, and F(n)=F(n-1)+F(n-2). What is F(20)? Convert the answer to base-36 (uppercase).",
     "example": "F(1)=1, F(2)=1, F(3)=2, F(4)=3 ..."},
    {"id": "r1p3", "seg": "1UP", "num": 2401,
     "title": "Power Play",
     "desc": "Compute 7 to the power of 4. Convert the answer to base-36 (uppercase).",
     "example": "Hint: 7 x 7 = 49."},
]

# Round 2 - Ciphers. Answer is the decoded plaintext.
R2 = [
    {"id": "r2c1", "seg": "RUSH",
     "title": "Caesar Cipher",
     "desc": "A message was encrypted with a Caesar cipher using a shift of +3 (each letter moved 3 forward). Decode it.",
     "cipher": "UXVK", "hint": "A -> D, B -> E. Reverse the shift."},
    {"id": "r2c2", "seg": "BYTE",
     "title": "Base64 Veil",
     "desc": "Decode this Base64 string. The answer is a common 4-letter computing term.",
     "cipher": "QllURQ==", "hint": "Base64 is an encoding, not encryption."},
    {"id": "r2c3", "seg": "NULL",
     "title": "Rot13 Mirror",
     "desc": "This text was ROT13 encoded and then reversed. Decode it fully to get the answer.",
     "cipher": "YYHA", "hint": "Reverse the string first, then ROT13 it."},
]

# Round 3 - Tech riddles.
R3 = [
    {"id": "r3r1", "seg": "192",
     "title": "The Digit Riddle",
     "desc": "I have three digits. The third is the sum of the first two. The second is three less than the first. The first is one more than the last. What am I?",
     "hint": "Let the first digit be x."},
    {"id": "r3r2", "seg": "ECHO",
     "title": "The Canyon Riddle",
     "desc": "I speak without a mouth and hear without ears. I have no body, but I come alive with the wind. What am I?",
     "hint": "It bounces off canyon walls."},
    {"id": "r3r3", "seg": "443",
     "title": "The Port Riddle",
     "desc": "I guard the web over TLS. Three digits. Which port am I?",
     "hint": "HTTPS uses me."},
    {"id": "r3r4", "seg": "TREE",
     "title": "The Structure Riddle",
     "desc": "I am rooted, I branch out, I grow in height, and I have leaves but I am not alive. What am I?",
     "hint": "Used in databases and file systems."},
]

# Round 4 - CTF questions.
R4 = [
    {"id": "r4q1", "seg": "BAK",
     "title": "Hidden Path",
     "desc": "A target server exposes /robots.txt which contains 'Disallow: /admin.bak'. What is the 3-letter file extension shown there?",
     "hint": "Extension only, no dot."},
    {"id": "r4q2", "seg": "OR1",
     "title": "SQL Injection",
     "desc": "Which 3-character SQL keyword pair is commonly used to bypass a login form's WHERE clause? (OR followed by the digit 1)",
     "hint": "Format: two letters then one digit."},
    {"id": "r4q3", "seg": "SHA",
     "title": "Hash Identification",
     "desc": "Name the 3-letter abbreviation of the cryptographic hash family commonly used for file integrity (e.g. sha-256).",
     "hint": "Secure Hash Algorithm."},
    {"id": "r4q4", "seg": "ROT",
     "title": "Rotation Cipher",
     "desc": "Which 3-letter abbreviation names the popular rotation cipher that shifts letters by 13?",
     "hint": "Also called the Caesar cipher variant."},
]

# Round 5 - live debugging. Correct fixed code produces the final flag.
FINAL_SEG = "QBIT"
FINAL_FLAG = "CTF{you_broke_the_matrix_and_took_first_place}"

ROUNDS = [
    {"n": 1, "slug": "round1", "name": "Logic Labyrinth", "icon": "\U0001F9E9", "items": R1,
     "brief": "Solve 3 logic puzzles. Each yields a code segment. Concatenate them in order to form the Round 2 unlock code."},
    {"n": 2, "slug": "round2", "name": "Cipher Vault", "icon": "\U0001F510", "items": R2,
     "brief": "Break 3 ciphers. Each decoded plaintext is a code segment. Concatenate them to unlock Round 3."},
    {"n": 3, "slug": "round3", "name": "Tech Riddles", "icon": "\U0001F9E0", "items": R3,
     "brief": "Answer 4 tech riddles. Each answer is a code segment. Concatenate them to unlock Round 4."},
    {"n": 4, "slug": "round4", "name": "Capture The Flag", "icon": "\U0001F6A9", "items": R4,
     "brief": "Answer 4 CTF questions. Each answer is a code segment. Concatenate them to unlock the Final Round."},
]

def answer_for(round_no, item_id):
    for rd in ROUNDS:
        if rd["n"] == round_no:
            for it in rd["items"]:
                if it["id"] == item_id:
                    return it["seg"]
    return None

def segments_for(round_no):
    for rd in ROUNDS:
        if rd["n"] == round_no:
            return [it["seg"] for it in rd["items"]]
    return []

# ============================ DB ============================
def get_db():
    if IS_PG:
        import psycopg2
        con = psycopg2.connect(DATABASE_URL)
        con.autocommit = True
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS teams (team TEXT PRIMARY KEY, at TIMESTAMP DEFAULT NOW())")
        cur.execute("CREATE TABLE IF NOT EXISTS progress (team TEXT, item TEXT, at TIMESTAMP DEFAULT NOW(), PRIMARY KEY (team, item))")
        cur.execute("CREATE TABLE IF NOT EXISTS winners (id SERIAL PRIMARY KEY, team TEXT, score INTEGER, at TIMESTAMP DEFAULT NOW())")
        cur.execute("CREATE TABLE IF NOT EXISTS settings (k TEXT PRIMARY KEY, v TEXT)")
        return con
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS teams (team TEXT PRIMARY KEY, at TEXT DEFAULT (datetime('now')))")
    con.execute("CREATE TABLE IF NOT EXISTS progress (team TEXT, item TEXT, at TEXT DEFAULT (datetime('now')), PRIMARY KEY (team, item))")
    con.execute("CREATE TABLE IF NOT EXISTS winners (id INTEGER PRIMARY KEY, team TEXT, score INTEGER, at TEXT DEFAULT (datetime('now')))")
    con.execute("CREATE TABLE IF NOT EXISTS settings (k TEXT PRIMARY KEY, v TEXT)")
    con.commit()
    return con

def q(con, sql, params=None):
    if IS_PG:
        sql = sql.replace("?", "%s")
        cur = con.cursor()
        cur.execute(sql, params)
        return cur
    if params is not None:
        return con.execute(sql, params)
    return con.execute(sql)

def commit(con):
    if not IS_PG:
        con.commit()

def get_team():
    return session.get("team") or request.cookies.get("hackquest_team")

def solved_items(team):
    if not team:
        return set()
    con = get_db()
    rows = q(con, "SELECT item FROM progress WHERE team=?", (team,)).fetchall()
    con.close()
    return {r[0] for r in rows}

def mark_solved(team, item):
    if not team:
        return
    con = get_db()
    q(con, "INSERT INTO teams (team) VALUES (?) ON CONFLICT DO NOTHING", (team,))
    q(con, "INSERT INTO progress (team,item) VALUES (?,?) ON CONFLICT DO NOTHING", (team, item))
    commit(con)
    con.close()

def round_complete(team, round_no):
    s = solved_items(team)
    return all(it["id"] in s for rd in ROUNDS if rd["n"] == round_no for it in rd["items"])

ROUND_SLUGS = {1: "round1", 2: "round2", 3: "round3", 4: "round4", 5: "final"}

def get_setting(key, default=""):
    con = get_db()
    row = q(con, "SELECT v FROM settings WHERE k=?", (key,)).fetchone()
    con.close()
    return row[0] if row else default

def set_setting(key, value):
    con = get_db()
    if IS_PG:
        con.cursor().execute("INSERT INTO settings (k,v) VALUES (?,?) ON CONFLICT (k) DO UPDATE SET v=EXCLUDED.v", (key, str(value)))
    else:
        con.execute("INSERT INTO settings (k,v) VALUES (?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (key, str(value)))
    commit(con)
    con.close()

def open_round():
    """Highest round the organiser has opened (default 1)."""
    try:
        return max(1, min(5, int(get_setting("open_round", "1"))))
    except (ValueError, TypeError):
        return 1

def unlocked_round(team):
    """Highest round a team may access.
    The team must have completed the previous round, and the organiser must have opened it."""
    if not team:
        return 0
    cap = open_round()
    reached = 1
    for n in range(1, 5):
        if round_complete(team, n) and n + 1 <= cap:
            reached = n + 1
        else:
            break
    return min(reached, 5)

def team_score(team):
    s = solved_items(team)
    total = 0
    for rd in ROUNDS:
        for it in rd["items"]:
            if it["id"] in s:
                total += {1: 100, 2: 200, 3: 300, 4: 400}[rd["n"]]
    return total

# ============================ UI ============================
PAGE = """<!DOCTYPE html><html><head><title>{{title}} - HackQuest CTF</title>
<style>
:root{--bg:#05080a;--panel:#0d141b;--border:#1e2a36;--green:#00ff9c;--cyan:#00e5ff;--red:#ff2d55;--amber:#ffb020;--blue:#2d9cff;--text:#d7e3ee;--muted:#7d8fa3;--mono:"JetBrains Mono","Fira Code",Consolas,monospace}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--mono);background:var(--bg);color:var(--text);line-height:1.7;min-height:100vh}
#matrix{position:fixed;inset:0;z-index:0;opacity:.12;pointer-events:none}
.scanlines{position:fixed;inset:0;z-index:1;pointer-events:none;background:repeating-linear-gradient(to bottom,rgba(0,0,0,0) 0 2px,rgba(0,0,0,.18) 3px,rgba(0,0,0,0) 4px)}
.topbar{position:sticky;top:0;z-index:100;display:flex;justify-content:space-between;align-items:center;padding:10px 24px;background:rgba(5,8,10,.93);backdrop-filter:blur(12px);border-bottom:1px solid var(--border);flex-wrap:wrap;gap:8px}
.brand{color:var(--green);font-weight:700;letter-spacing:2px;text-shadow:0 0 12px rgba(0,255,156,.6)}
.topbar nav{display:flex;gap:4px;flex-wrap:wrap}
.topbar nav a{color:var(--muted);text-decoration:none;padding:5px 9px;font-size:.8rem;border-radius:4px}
.topbar nav a:hover{color:var(--green);background:rgba(0,255,156,.08)}
.wrap{position:relative;z-index:2;max-width:960px;margin:0 auto;padding:28px 20px 60px}
h1{color:var(--green);font-size:1.9rem;margin-bottom:6px;text-shadow:0 0 18px rgba(0,255,156,.4)}
h2{color:var(--green);font-size:1.35rem;margin:18px 0 12px;text-shadow:0 0 14px rgba(0,255,156,.35)}
.sub{color:var(--muted);margin-bottom:18px}
.banner{background:var(--panel);border:1px solid var(--border);border-left:3px solid var(--green);border-radius:6px;padding:10px 14px;margin-bottom:18px;font-size:.85rem}
.banner.warn{border-left-color:var(--amber);color:var(--amber)}
.card{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:20px;margin-bottom:14px}
.card.solved{border-color:var(--green-dim);background:linear-gradient(135deg,rgba(0,255,156,.06),transparent)}
.locked{opacity:.42;pointer-events:none}
.lockbadge{display:inline-block;background:rgba(255,45,85,.15);color:var(--red);border:1px solid rgba(255,45,85,.4);padding:3px 10px;border-radius:12px;font-size:.72rem;font-weight:700}
.donesbadge{display:inline-block;background:rgba(0,255,156,.15);color:var(--green);border:1px solid var(--green-dim);padding:3px 10px;border-radius:12px;font-size:.72rem;font-weight:700}
code,.mono{color:var(--amber);background:rgba(255,176,32,.1);padding:2px 6px;border-radius:4px;font-family:var(--mono)}
pre{background:#080d12;border:1px solid var(--border);padding:16px;border-radius:8px;overflow-x:auto;white-space:pre-wrap;margin:12px 0;color:#c9e4d8}
input{padding:11px;margin:8px 0;background:#080d12;border:1px solid var(--border);color:var(--text);border-radius:6px;width:100%;max-width:460px;font-family:var(--mono);font-size:.92rem}
input:focus{outline:none;border-color:var(--green);box-shadow:0 0 12px rgba(0,255,156,.3)}
button{padding:11px 24px;background:var(--green);color:#04120b;border:none;cursor:pointer;border-radius:6px;font-family:var(--mono);font-weight:700;box-shadow:0 0 16px rgba(0,255,156,.4)}
button:hover{box-shadow:0 0 30px rgba(0,255,156,.75)}
button.ghost{background:transparent;color:var(--muted);border:1px solid var(--border);box-shadow:none;font-weight:400}
button.ghost:hover{color:var(--green);border-color:var(--green-dim);box-shadow:none}
.flag{background:linear-gradient(135deg,rgba(0,255,156,.22),rgba(0,255,156,.05));border:1px solid var(--green);padding:18px;border-radius:10px;margin:16px 0;font-size:1.15em;color:var(--green);text-shadow:0 0 14px rgba(0,255,156,.6);word-break:break-all}
.segment{display:inline-block;background:rgba(0,255,156,.12);border:1px solid var(--green-dim);color:var(--green);padding:6px 14px;border-radius:6px;font-weight:700;letter-spacing:2px;margin:4px 6px 4px 0;font-size:1.05rem}
.err{color:var(--red);font-size:.9rem;margin-top:6px}
.ok{color:var(--green);font-size:.9rem;margin-top:6px}
table{border-collapse:collapse;width:100%;margin:12px 0;background:var(--panel);border:1px solid var(--border);border-radius:10px;overflow:hidden;font-size:.88rem}
th,td{border:1px solid var(--border);padding:10px 12px;text-align:left}
th{background:#080d12;color:var(--green);font-size:.75rem;text-transform:uppercase;letter-spacing:1px}
tbody tr:last-child td{border-bottom:none}
.grid{display:grid;gap:14px}
.grid.rounds{grid-template-columns:repeat(auto-fit,minmax(240px,1fr))}
.rcard{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:18px;text-decoration:none;display:block;color:var(--text);transition:all .22s}
.rcard:hover{border-color:var(--green-dim);transform:translateY(-3px);box-shadow:0 8px 24px rgba(0,255,156,.12)}
.rcard.locked{opacity:.4;pointer-events:none}
.rnum{font-size:.72rem;color:var(--muted);letter-spacing:1px;text-transform:uppercase}
.rname{color:var(--green);font-weight:700;font-size:1.06rem;margin:4px 0}
.rprog{font-size:.8rem;color:var(--muted)}
.rprog b{color:var(--green)}
.unlock{margin-top:18px;padding:16px;background:rgba(0,229,255,.06);border:1px solid rgba(0,229,255,.3);border-radius:10px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0}
.chip{font-family:var(--mono);background:#080d12;border:1px dashed var(--border);color:var(--muted);padding:6px 12px;border-radius:6px;font-size:.9rem;letter-spacing:2px}
.chip.got{border:1px solid var(--green-dim);color:var(--green);background:rgba(0,255,156,.1);border-style:solid;font-weight:700}
a{color:var(--cyan)}
.hintbtn{background:none;border:none;color:var(--muted);font-size:.8rem;cursor:pointer;padding:6px 0;text-decoration:underline;font-family:var(--mono)}
.hint{color:var(--amber);font-size:.85rem;margin-top:6px}
@media(max-width:720px){.wrap{padding:20px 14px 50px}}
</style></head>
<body>
<canvas id="matrix"></canvas><div class="scanlines"></div>
<div class="topbar">
  <span class="brand">&#9619;&#9618;&#9617; HACKQUEST</span>
  <nav>
    <a href="/">Arena</a><a href="/round1">R1</a><a href="/round2">R2</a><a href="/round3">R3</a>
    <a href="/round4">R4</a><a href="/final">Final</a><a href="/join">Join</a><a href="/leaderboard">Scoreboard</a>
  </nav>
</div>
<div class="wrap">{{body|safe}}</div>
<script>(function(){var c=document.getElementById("matrix"),x=c.getContext("2d"),ch="01ABCDEF<>/\\{}[]$#@%&*+=?!;:. ",fs=14,cols,drops;function rs(){c.width=innerWidth;c.height=innerHeight;cols=Math.floor(c.width/fs);drops=Array(cols).fill(1).map(function(){return Math.random()*-50})}rs();addEventListener("resize",rs);setInterval(function(){x.fillStyle="rgba(5,8,10,.08)";x.fillRect(0,0,c.width,c.height);x.fillStyle="#00ff9c";x.font=fs+"px monospace";for(var i=0;i<drops.length;i++){x.fillText(ch[Math.floor(Math.random()*ch.length)],i*fs,drops[i]*fs);if(drops[i]*fs>c.height&&Math.random()>.975)drops[i]=0;drops[i]++}},50)})();</script>
</body></html>"""

def page(title, body):
    team = get_team()
    if team:
        un = unlocked_round(team)
        banner = (f"<div class='banner'>Playing as <b style='color:var(--green)'>{team}</b> &middot; "
                  f"Round <b style='color:var(--green)'>{min(un,5)}</b>/5 unlocked &middot; "
                  f"Score <b style='color:var(--green)'>{team_score(team)}</b> &middot; "
                  f"<a href='/join'>switch</a> &middot; <a href='/leaderboard'>scoreboard</a></div>")
    else:
        banner = "<div class='banner warn'>&#9888; You haven't joined a team. <a href='/join'>Join a team</a> to unlock rounds and record scores.</div>"
    announce = get_setting("announce", "")
    if announce:
        banner += f"<div class='flag' style='font-size:.95em'>&#128227; <b>Announcement:</b> {announce}</div>"
    return render_template_string(PAGE, title=title, body=banner + body)

# ============================ ROUTES ============================
@app.route("/")
def arena():
    team = get_team()
    un = unlocked_round(team) if team else 0
    cards = ""
    for rd in ROUNDS + [{"n": 5, "slug": "final", "name": "Live Debugging Finale", "icon": "\U0001F6E0\uFE0F", "items": []}]:
        avail = team and un >= rd["n"]
        total = len(rd["items"])
        s = solved_items(team) if team else set()
        done = sum(1 for it in rd["items"] if it["id"] in s)
        prog = f"<b>{done}/{total}</b>" if total else ("&#9989; complete" if avail else "&mdash;")
        lock = "" if avail else '<div class="lockbadge">LOCKED</div>'
        cards += (f'<a class="rcard {"locked" if not avail else ""}" href="/{rd["slug"]}">'
                  f'<div class="rnum">ROUND {rd["n"]}</div>'
                  f'<div class="rname">{rd["icon"]} {rd["name"]}</div>'
                  f'<div class="rprog">Progress: {prog}</div>{lock}</a>')
    return page("Arena", f"""
    <h1>&#128274; HackQuest Arena</h1>
    <p class="sub">5 escalating rounds. Solve each challenge to reveal its code segment. Segments concatenate into the code that unlocks the next round.</p>
    <div class="grid rounds">{cards}</div>
    <div class="unlock"><b style='color:var(--cyan)'>&#128274; How progression works</b>
    <p style='font-size:.88rem;color:var(--muted);margin-top:8px'>Each round's challenges are solved one at a time. Every correct solve reveals a <b>code segment</b>. When all segments of a round are collected, they concatenate (in order) to form the unlock code for the next round &mdash; which is also shown to you automatically. Answers are never revealed.</p></div>
    """)

@app.route("/join", methods=["GET", "POST"])
def join():
    if request.method == "POST":
        team = request.form.get("team", "").strip() or "Anonymous"
        session["team"] = team
        con = get_db()
        q(con, "INSERT INTO teams (team) VALUES (?) ON CONFLICT DO NOTHING", (team,))
        commit(con); con.close()
        resp = make_response(page("Joined", f"<p>Welcome <b style='color:var(--green)'>{team}</b>. "
                                             f"Round 1 is now unlocked. <a href='/round1'>Start &#9654;</a></p>"))
        resp.set_cookie("hackquest_team", team, max_age=30*24*3600)
        return resp
    return page("Join Team", "<form method='post'><input name='team' placeholder='Team name' required>"
                             "<button>Join Arena</button></form>")

@app.route("/leaderboard")
def leaderboard():
    con = get_db()
    rows = q(con, """
        SELECT t.team,
               COUNT(p.item) AS solves,
               SUM(CASE WHEN p.item LIKE 'r1%' THEN 100
                        WHEN p.item LIKE 'r2%' THEN 200
                        WHEN p.item LIKE 'r3%' THEN 300
                        WHEN p.item LIKE 'r4%' THEN 400
                        WHEN p.item = 'final' THEN 500 ELSE 0 END) AS score
        FROM teams t LEFT JOIN progress p ON p.team = t.team
        GROUP BY t.team ORDER BY score DESC, MIN(COALESCE(p.at, t.at)) ASC
    """).fetchall()
    con.close()
    team = get_team()
    body = "<table><tr><th>Rank</th><th>Team</th><th>Solves</th><th>Score</th></tr>"
    for i, (t, s, sc) in enumerate(rows, 1):
        mark = " &#9654;" if team and t == team else ""
        body += f"<tr><td>{i}</td><td>{t}{mark}</td><td>{s}</td><td>{sc or 0}</td></tr>"
    body += "</table>" if rows else "<p>No teams yet. <a href='/join'>Join first</a></p>"
    if team:
        body += f"<p style='margin-top:14px'>You are playing as <b style='color:var(--green)'>{team}</b>. <a href='/join'>Switch team</a></p>"
    return page("Leaderboard", body)

def round_page(round_no):
    rd = [r for r in ROUNDS if r["n"] == round_no][0]
    team = get_team()
    if not team:
        return page(rd["name"], "<p><a href='/join'>Join a team</a> to access the rounds.</p>"), 403
    un = unlocked_round(team)
    if un < round_no:
        return page("Locked", f"<div class='lockbadge'>&#128274; LOCKED</div><p>Complete Round {round_no-1} first.</p>"), 403
    s = solved_items(team)
    segs = segments_for(round_no)
    chips = ""
    for i, it in enumerate(rd["items"]):
        got = it["id"] in s
        chips += f"<span class='chip {'got' if got else ''}'>{it['seg'] if got else '????'}</span>"
    done = sum(1 for it in rd["items"] if it["id"] in s)
    body = f"""
    <h1>{rd['icon']} Round {round_no}: {rd['name']}</h1>
    <p class="sub">{rd['brief']}</p>
    <div class="unlock"><b style='color:var(--cyan)'>&#127919; Your segments ({done}/{len(rd['items'])})</b>
    <div class="chips">{chips}</div>
    {'<p style="color:var(--green);font-weight:700">All segments collected! Next unlock code: <code>' + ''.join(segs) + '</code></p>' if done == len(rd['items']) else ''}</div>
    """
    for it in rd["items"]:
        solved = it["id"] in s
        extra = ""
        if "cipher" in it:
            extra += f"<pre>{it['cipher']}</pre>"
        elif "num" in it:
            extra += f"<pre>1 + 2 + 3 + ... + N</pre>" if it["id"] == "r1p1" else ""
        if "hint" in it and not solved:
            extra += (f"<button class='hintbtn' onclick=\"this.nextElementSibling.style.display="
                      f"'{'none' if False else 'block'}'\">Show hint</button>"
                      f"<div class='hint' style='display:none'>{it['hint']}</div>")
        if solved:
            body += (f"<div class='card solved'><span class='donesbadge'>&#10003; SOLVED</span>"
                     f"<div style='margin-top:10px'><b style='color:var(--green)'>{it['title']}</b><br>"
                     f"<span style='color:var(--muted);font-size:.85rem'>Code segment:</span> "
                     f"<span class='segment'>{it['seg']}</span></div></div>")
        else:
            body += (f"<div class='card'><b>{it['title']}</b>"
                     f"<p style='font-size:.92rem'>{it['desc']}</p>{extra}"
                     f"<form method='post' action='/{rd['slug']}/{it['id']}'>"
                     f"<input name='answer' placeholder='Enter code / answer' required>"
                     f"<button>Submit</button></form></div>")
    return page(rd["name"], body)

@app.route("/round1", methods=["GET"])
def round1(): return round_page(1)
@app.route("/round2", methods=["GET"])
def round2(): return round_page(2)
@app.route("/round3", methods=["GET"])
def round3(): return round_page(3)
@app.route("/round4", methods=["GET"])
def round4(): return round_page(4)

@app.route("/round1/<item>", methods=["POST"])
def submit1(item): return handle_submit(1, item)
@app.route("/round2/<item>", methods=["POST"])
def submit2(item): return handle_submit(2, item)
@app.route("/round3/<item>", methods=["POST"])
def submit3(item): return handle_submit(3, item)
@app.route("/round4/<item>", methods=["POST"])
def submit4(item): return handle_submit(4, item)

def handle_submit(round_no, item_id):
    team = get_team()
    rd = [r for r in ROUNDS if r["n"] == round_no][0]
    if not team:
        return page("Join", "<p><a href='/join'>Join a team</a> first.</p>"), 403
    if unlocked_round(team) < round_no:
        return page("Locked", "<div class='lockbadge'>LOCKED</div>"), 403
    item = next((it for it in rd["items"] if it["id"] == item_id), None)
    if not item:
        return page("Error", "<p>Unknown challenge.</p>"), 404
    guess = request.form.get("answer", "").strip()
    correct = guess.upper().replace("-", "").replace(" ", "") == item["seg"].upper()
    if correct:
        mark_solved(team, item_id)
        s = solved_items(team)
        done = sum(1 for it in rd["items"] if it["id"] in s)
        msg = f"<div class='flag'>&#10003; Correct! Your code segment: <b>{item['seg']}</b></div>"
        if done == len(rd["items"]):
            code = "".join(segments_for(round_no))
            nxt_no = round_no + 1
            nxt = ROUND_SLUGS[nxt_no]
            # Only offer the link if the organiser has actually opened the next round.
            if unlocked_round(team) >= nxt_no:
                msg += (f"<div class='unlock'><b style='color:var(--cyan)'>&#127881; Round {round_no} complete! "
                        f"Your unlock code: <code>{code}</code></b>"
                        f"<p style='margin-top:12px'><a href='/{nxt}' style='background:var(--green);color:#04120b;"
                        f"padding:11px 24px;border-radius:6px;font-weight:700;text-decoration:none'>"
                        f"Enter Round {nxt_no} &#9654;</a></p></div>")
            else:
                msg += (f"<div class='unlock'><b style='color:var(--cyan)'>&#127881; Round {round_no} complete! "
                        f"Your unlock code: <code>{code}</code></b>"
                        f"<p style='margin-top:10px;color:var(--muted)'>&#128274; <b>Round {nxt_no} is not open yet.</b> "
                        f"The organiser will open it — this page updates automatically, or check the Arena.</p></div>")
        else:
            msg += f"<p><a href='/{rd['slug']}'>&#8592; Back to Round {round_no}</a></p>"
        return page(item["title"], msg)
    return page(item["title"], f"<div class='err'>&#10007; Incorrect. Try again. Answers are never shown.</div>"
                               f"<p><a href='/{rd['slug']}'>&#8592; Back to Round {round_no}</a></p>")

def check_debug_fix(code):
    """Validate the submitted fixed function.
    Whitespace, indentation, newlines and any surrounding wrapper are ignored,
    so any reasonable formatting of a correct fix is accepted."""
    if not code:
        return False
    s = "".join(code.split()).lower()
    # Must actually sum 1..100 - the broken version multiplies 1..10.
    if "sum(range(1,101))" in s or "sum(range(1,100))+100" in s:
        return True
    return False

@app.route("/final", methods=["GET", "POST"])
def final_round():
    team = get_team()
    if not team:
        return page("Final Round", "<p><a href='/join'>Join a team</a> to access the final round.</p>"), 403
    if unlocked_round(team) < 5:
        return page("Locked", "<div class='lockbadge'>&#128274; LOCKED</div><p>Complete Rounds 1-4 first.</p>"), 403
    s = solved_items(team)
    if "final" in s:
        pos = q(get_db(), "SELECT id FROM winners WHERE team=? ORDER BY id ASC LIMIT 1", (team,)).fetchone()
        total_winners = q(get_db(), "SELECT COUNT(*) FROM winners").fetchone()[0]
        return page("Final", f"<div class='flag'>{FINAL_FLAG}</div>"
                              f"<div class='unlock'><b style='color:var(--cyan)'>&#127942; Winning Position</b><br>"
                              f"Position: <b style='color:var(--amber)'>#{pos[0] if pos else '?'}</b> of "
                              f"{total_winners} winners</div>")
    if request.method == "POST":
        code = request.form.get("code", "").strip()
        ok = check_debug_fix(code)
        if ok:
            mark_solved(team, "final")
            con = get_db()
            q(con, "INSERT INTO winners (team, score) VALUES (?,?)", (team, team_score(team)))
            commit(con); con.close()
            pos = q(get_db(), "SELECT id FROM winners WHERE team=? ORDER BY id ASC LIMIT 1", (team,)).fetchone()
            return page("Final", f"<div class='flag'>{FINAL_FLAG}</div>"
                                  f"<div class='unlock'><b style='color:var(--cyan)'>&#127942; Winning Position</b><br>"
                                  f"Position: <b style='color:var(--amber)'>#{pos[0] if pos else '?'}</b></div>")
        return page("Final", "<div class='err'>&#10007; Code still fails the tests.</div>"
                         "<div class='unlock'><b style='color:var(--cyan)'>&#128188; Grader rules</b>"
                         "<ul style='margin:10px 0 0 18px;color:var(--muted);font-size:.9rem'>"
                         "<li>Spaces, tabs and newlines are ignored &mdash; formatting does not matter.</li>"
                         "<li>Submit only the <b>body</b> that computes the total. A <code>def fix():</code> wrapper is optional.</li>"
                         "<li>It must <b>sum</b> 1 to 100 &mdash; the broken version multiplies 1 to 10.</li>"
                         "</ul></div>")
    return page("Final Round", f"""
    <h1>&#128295; Final Round: Live Coding Debugging</h1>
    <p class="sub">This code fails 2 of 5 test cases. Fix it and paste the exact fixed <code>def fix():</code> line.</p>
    <pre>from functools import reduce

def fix():
    # BUG: uses the wrong bound, and ignores `total`
    total = reduce(lambda a, b: a * b, range(1, 11))
    return total

# tests:
# fix() == 55      -> FAIL (returns 3628800)
# fix() == 5050    -> FAIL</pre>
    <div class="unlock"><b style='color:var(--cyan)'>&#128188; The bug</b>
    <p style='font-size:.9rem'>Two bugs: (1) it multiplies instead of summing. (2) wrong range. Replace the entire
    <code>def fix():</code> block with a correct one. The grader strips whitespace, so indentation and line breaks don't matter &mdash; just write it as one continuous expression assigned to <code>total</code>.</p></div>
    <form method='post'><input name='code' placeholder='paste your corrected fix() here - spacing does not matter' required style="max-width:100%"><button>Run Tests</button></form>
    """)

# ============================ ORGANISER PANEL ============================
PANEL_HTML = open(os.path.join(os.path.dirname(__file__), "panel.html"), encoding="utf-8").read()

def org_required():
    return bool(session.get("org"))

def org_guard():
    if not org_required():
        return page("Organiser Login",
                    "<div class='lockbadge'>&#128274; Organiser access only</div>"
                    "<p>Enter the organiser token to control the event.</p>"
                    "<form method='post'><input name='token' type='password' placeholder='Organiser token' required>"
                    "<button>Sign in</button></form>"
                    "<p style='margin-top:14px'><a href='/'>&#8592; Back to arena</a></p>"), 403
    return None

@app.route("/organiser", methods=["GET", "POST"])
def organiser_login():
    if request.method == "POST":
        if request.form.get("token", "") == ADMIN_TOKEN:
            session["org"] = True
            return page("Organiser", "<div class='flag'>&#10003; Signed in as organiser.</div>"
                                    "<p><a href='/organiser/panel'>&#9654; Open control panel</a></p>")
        return page("Organiser Login", "<div class='err'>&#10007; Invalid token.</div>"
                      "<form method='post'><input name='token' type='password' placeholder='Organiser token' required>"
                      "<button>Sign in</button></form>"), 403
    return org_guard()

@app.route("/organiser/logout")
def organiser_logout():
    session.pop("org", None)
    return page("Signed out", "<div class='flag'>&#10003; Organiser signed out.</div>")

@app.route("/organiser/panel")
def organiser_panel():
    guard = org_guard()
    if guard:
        return guard
    cur = open_round()
    announce = get_setting("announce", "")
    con = get_db()
    rows = q(con, "SELECT team, item FROM progress").fetchall()
    con.close()
    teams = {}
    for t, item in rows:
        teams.setdefault(t, set()).add(item)
    board = sorted(((team_score(t), t, items) for t, items in teams.items()), key=lambda x: -x[0])
    rows_html = ""
    for s, t, items in board:
        marks = ""
        for n in range(1, 5):
            ids = [i["id"] for rd in ROUNDS if rd["n"] == n for i in rd["items"]]
            got = sum(1 for i in ids if i in items)
            col = "var(--green)" if got == len(ids) else "var(--muted)"
            marks += f"<td style='color:{col}'>{got}/{len(ids)}</td>"
        fin = "final" in items
        rows_html += (f"<tr><td><b>{t}</b></td>{marks}"
                      f"<td style='color:{'var(--green)' if fin else 'var(--muted)'}'>{'&#10003;' if fin else '&#8212;'}</td>"
                      f"<td><b style='color:var(--amber)'>{s + (500 if fin else 0)}</b></td>"
                      f"<td><form method='post' action='/organiser/reset-team' style='display:inline'>"
                      f"<input type='hidden' name='team' value='{t}'>"
                      f"<button class='ghost' style='padding:5px 10px;font-size:.75rem'>reset</button>"
                      f"</form></td></tr>")
    if not rows_html:
        rows_html = "<tr><td colspan='7' style='color:var(--muted)'>No teams yet</td></tr>"
    btns = ""
    for n in range(1, 6):
        label = "Final Round" if n == 5 else f"Round {n}"
        style = "background:var(--green);color:#04120b" if cur == n else ""
        cls = "" if cur == n else "class='ghost'"
        btns += (f"<form method='post' action='/organiser/open' style='display:inline'>"
                 f"<input type='hidden' name='n' value='{n}'>"
                 f"<button {cls} style='margin:4px;{style}'>{label}</button></form>")
    html = (PANEL_HTML
            .replace("@@CURRENT@@", "Final Round" if cur == 5 else f"Round {cur}")
            .replace("@@BTNS@@", btns)
            .replace("@@ROWS@@", rows_html)
            .replace("@@ANNOUNCE@@", announce))
    return page("Organiser Panel", html)

@app.route("/organiser/open", methods=["POST"])
def organiser_open():
    if not org_required():
        return page("Denied", "<p>Organiser only.</p>"), 403
    n = request.form.get("n", "1")
    if n.isdigit() and 1 <= int(n) <= 5:
        set_setting("open_round", int(n))
    return redirect("/organiser/panel")

@app.route("/organiser/announce", methods=["POST"])
def organiser_announce():
    if not org_required():
        return page("Denied", "<p>Organiser only.</p>"), 403
    set_setting("announce", request.form.get("msg", "").strip()[:300])
    return redirect("/organiser/panel")

@app.route("/organiser/clear-announce", methods=["POST"])
def organiser_clear_announce():
    if not org_required():
        return page("Denied", "<p>Organiser only.</p>"), 403
    set_setting("announce", "")
    return redirect("/organiser/panel")

@app.route("/organiser/reset-team", methods=["POST"])
def organiser_reset_team():
    if not org_required():
        return page("Denied", "<p>Organiser only.</p>"), 403
    team = request.form.get("team", "")
    con = get_db()
    q(con, "DELETE FROM progress WHERE team=?", (team,))
    q(con, "DELETE FROM winners WHERE team=?", (team,))
    commit(con); con.close()
    return redirect("/organiser/panel")

@app.route("/organiser/reset-all", methods=["POST"])
def organiser_reset_all():
    if not org_required():
        return page("Denied", "<p>Organiser only.</p>"), 403
    con = get_db()
    for t in ("progress", "winners", "teams"):
        q(con, f"DELETE FROM {t}") if IS_PG else con.execute(f"DELETE FROM {t}")
    commit(con); con.close()
    set_setting("open_round", 1)
    set_setting("announce", "")
    return redirect("/organiser/panel")

@app.route("/admin")
def admin_panel():
    if request.args.get("token") != ADMIN_TOKEN:
        return page("Admin", "<p>Invalid token.</p>"), 403
    con = get_db()
    rows = q(con, """
        SELECT t.team, COUNT(p.item) AS solves,
        SUM(CASE WHEN p.item LIKE 'r1%' THEN 100 WHEN p.item LIKE 'r2%' THEN 200
                 WHEN p.item LIKE 'r3%' THEN 300 WHEN p.item LIKE 'r4%' THEN 400
                 WHEN p.item='final' THEN 500 ELSE 0 END) AS score
        FROM teams t LEFT JOIN progress p ON p.team=t.team GROUP BY t.team ORDER BY score DESC
    """).fetchall()
    con.close()
    body = "<table><tr><th>Team</th><th>Solves</th><th>Score</th></tr>"
    for t, s, sc in rows:
        body += f"<tr><td>{t}</td><td>{s}</td><td>{sc or 0}</td></tr>"
    body += "</table>" if rows else "<p>No teams.</p>"
    body += ("<hr><h3>Round Management</h3>"
             f"<p>Clear all teams, progress and winners to start fresh:</p>"
             f"<p><a href='/admin/reset?token={ADMIN_TOKEN}'>&#128465; Clear Leaderboard</a></p>")
    return page("Admin", body)

@app.route("/admin/reset")
def admin_reset():
    if request.args.get("token") != ADMIN_TOKEN:
        return page("Admin", "<p>Invalid token.</p>"), 403
    con = get_db()
    for t in ("progress", "winners", "teams"):
        q(con, f"DELETE FROM {t}") if IS_PG else con.execute(f"DELETE FROM {t}")
    commit(con); con.close()
    return page("Reset", "<div class='flag'>&#10003; Cleared.</div>")

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=int(PORT))