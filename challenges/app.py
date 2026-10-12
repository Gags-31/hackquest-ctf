"""HackQuest CTF - Web Security & Ethical Hacking Challenge Lab
15 challenges. Run: python app.py -> http://localhost:5000
Uses PostgreSQL when DATABASE_URL is set (Render), otherwise local SQLite.
"""
import os
import sqlite3
import base64
import hashlib
import hmac
import json
from flask import Flask, request, render_template_string, session, make_response

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "hackquest_ctf_secret")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "hackquest-admin-2026")
DB = os.path.join(os.path.dirname(__file__), "ctf.db")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

DATABASE_URL = os.environ.get("DATABASE_URL", "")
IS_PG = DATABASE_URL.startswith("postgres")
PORT = os.environ.get("PORT", "5000")

PAGE = """<!DOCTYPE html><html><head><title>{{title}} — HackQuest CTF</title>
<style>
:root{--bg:#05080a;--panel:#0d141b;--border:#1e2a36;--green:#00ff9c;--cyan:#00e5ff;--red:#ff2d55;--amber:#ffb020;--blue:#2d9cff;--text:#d7e3ee;--muted:#7d8fa3;--mono:"JetBrains Mono","Fira Code",Consolas,monospace}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--mono);background:var(--bg);color:var(--text);line-height:1.7;min-height:100vh}
#matrix{position:fixed;inset:0;z-index:0;opacity:.12;pointer-events:none}
.scanlines{position:fixed;inset:0;z-index:1;pointer-events:none;background:repeating-linear-gradient(to bottom,rgba(0,0,0,0) 0 2px,rgba(0,0,0,.18) 3px,rgba(0,0,0,0) 4px)}
.topbar{position:sticky;top:0;z-index:100;display:flex;justify-content:space-between;align-items:center;padding:10px 24px;background:rgba(5,8,10,.92);backdrop-filter:blur(12px);border-bottom:1px solid var(--border)}
.brand{color:var(--green);font-weight:700;letter-spacing:2px;text-shadow:0 0 12px rgba(0,255,156,.6)}
.topbar a{color:var(--muted);text-decoration:none;padding:5px 9px;font-size:.8rem;border-radius:4px}
.topbar a:hover{color:var(--green);background:rgba(0,255,156,.08)}
.wrap{position:relative;z-index:2;max-width:880px;margin:0 auto;padding:28px 20px 50px}
h2{color:var(--green);font-size:1.5rem;margin-bottom:16px;letter-spacing:1px;text-shadow:0 0 16px rgba(0,255,156,.4)}
p{margin:10px 0}
a{color:var(--cyan)}
code{color:var(--amber);background:rgba(255,176,32,.1);padding:1px 5px;border-radius:4px}
pre{background:var(--panel);border:1px solid var(--border);padding:14px;border-radius:8px;overflow-x:auto;white-space:pre-wrap;margin:10px 0}
input,select{padding:9px;margin:5px 0;background:var(--panel);border:1px solid var(--border);color:var(--text);border-radius:6px;width:100%;max-width:420px;font-family:var(--mono);font-size:.88rem}
input:focus,select:focus{outline:none;border-color:var(--green);box-shadow:0 0 10px rgba(0,255,156,.3)}
button{padding:10px 22px;background:var(--green);color:#04120b;border:none;cursor:pointer;border-radius:6px;margin:6px 0;font-family:var(--mono);font-weight:700;font-size:.88rem;box-shadow:0 0 16px rgba(0,255,156,.4)}
button:hover{box-shadow:0 0 28px rgba(0,255,156,.7)}
.flag{background:linear-gradient(135deg,rgba(0,255,156,.2),rgba(0,255,156,.05));border:1px solid var(--green);padding:16px;border-radius:10px;margin:14px 0;font-size:1.15em;color:var(--green);text-shadow:0 0 12px rgba(0,255,156,.6)}
.banner{background:var(--panel);border:1px solid var(--border);border-left:3px solid var(--green);border-radius:6px;padding:10px 14px;margin-bottom:18px;font-size:.85rem}
.banner.warn{border-left-color:var(--amber);color:var(--amber)}
table{border-collapse:collapse;width:100%;margin:12px 0;background:var(--panel);border:1px solid var(--border);border-radius:10px;overflow:hidden;font-size:.88rem}
th,td{border:1px solid var(--border);padding:10px 12px;text-align:left}
th{background:var(--bg);color:var(--green);font-size:.75rem;text-transform:uppercase;letter-spacing:1px}
tbody tr{transition:background .15s}tbody tr:hover{background:rgba(0,255,156,.05)}
tbody tr:last-child td{border-bottom:none}
.comment{background:var(--panel);border:1px solid var(--border);border-left:3px solid var(--cyan);padding:10px 14px;border-radius:6px;margin:6px 0}
.pill{display:inline-block;padding:2px 10px;border-radius:12px;font-size:.7rem;font-weight:700;text-transform:uppercase}
.pill.easy{background:rgba(0,255,156,.15);color:var(--green)}
.pill.medium{background:rgba(255,176,32,.15);color:var(--amber)}
.pill.advanced{background:rgba(45,156,255,.15);color:var(--blue)}
.pill.hard{background:rgba(255,45,85,.15);color:var(--red)}
.backlink{display:inline-block;margin-top:20px;color:var(--muted);text-decoration:none;font-size:.85rem}
.backlink:hover{color:var(--green)}
</style></head>
<body>
<canvas id="matrix"></canvas>
<div class="scanlines"></div>
<div class="topbar">
  <span class="brand">▓▒░ HACKQUEST</span>
  <div>
    <a href="/">Challenges</a>
    <a href="/join">Join</a>
    <a href="/leaderboard">Scoreboard</a>
  </div>
</div>
<div class="wrap">
{{body|safe}}
</div>
<script>
(function(){var c=document.getElementById("matrix"),x=c.getContext("2d"),ch="アイウエオカキクケコサシスセソ01ABCDEF<>/\\\\{}[]$#@%&*+=?!;:.",cols,drops,fs=14;
function rs(){c.width=innerWidth;c.height=innerHeight;cols=Math.floor(c.width/fs);drops=Array(cols).fill(1).map(function(){return Math.random()*-50})}
rs();addEventListener("resize",rs);
setInterval(function(){x.fillStyle="rgba(5,8,10,.08)";x.fillRect(0,0,c.width,c.height);x.fillStyle="#00ff9c";x.font=fs+"px monospace";
for(var i=0;i<drops.length;i++){x.fillText(ch[Math.floor(Math.random()*ch.length)],i*fs,drops[i]*fs);
if(drops[i]*fs>c.height&&Math.random()>.975)drops[i]=0;drops[i]++}},50)})();
</script>
</body></html>"""

def get_team():
    """Get the current team from the session, falling back to a persistent cookie."""
    return session.get("team") or request.cookies.get("hackquest_team")

def page(title, body):
    team = get_team()
    if team:
        banner = f"<div class='banner'>Playing as: <b style='color:var(--green)'>{team}</b> · <a href='/join'>switch</a> · <a href='/leaderboard'>scoreboard</a></div>"
    else:
        banner = "<div class='banner warn'>⚠ You haven't joined a team. <a href='/join'>Join a team</a> to record scores.</div>"
    return render_template_string(PAGE, title=title, body=f"<h2>{title}</h2>" + banner + body)

def get_db():
    if IS_PG:
        import psycopg2
        con = psycopg2.connect(DATABASE_URL)
        con.autocommit = True
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, password TEXT, role TEXT, secret TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, name TEXT, description TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS comments (id SERIAL PRIMARY KEY, text TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS teams (team TEXT PRIMARY KEY, at TIMESTAMP DEFAULT NOW())")
        cur.execute("CREATE TABLE IF NOT EXISTS scores (id SERIAL PRIMARY KEY, team TEXT, challenge TEXT, points INTEGER, at TIMESTAMP DEFAULT NOW())")
        for s in [(1,'alice','password123','user','CTF{alice_secret}'),(2,'admin','admin123','admin','CTF{admin_secret}')]:
            cur.execute("INSERT INTO users (id,name,password,role,secret) VALUES (%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING", s)
        for s in [(1,'Widget','A fine widget'),(2,'Gadget','A fine gadget')]:
            cur.execute("INSERT INTO items (id,name,description) VALUES (%s,%s,%s) ON CONFLICT (id) DO NOTHING", s)
        return con
    else:
        con = sqlite3.connect(DB)
        con.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, password TEXT, role TEXT, secret TEXT)")
        con.execute("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, name TEXT, description TEXT)")
        con.execute("CREATE TABLE IF NOT EXISTS comments (id INTEGER PRIMARY KEY, text TEXT)")
        con.execute("CREATE TABLE IF NOT EXISTS teams (team TEXT PRIMARY KEY, at TEXT DEFAULT (datetime('now')))")
        con.execute("CREATE TABLE IF NOT EXISTS scores (id INTEGER PRIMARY KEY, team TEXT, challenge TEXT, points INTEGER, at TEXT DEFAULT (datetime('now')))")
        con.execute("INSERT OR IGNORE INTO users VALUES (1,'alice','password123','user','CTF{alice_secret}')")
        con.execute("INSERT OR IGNORE INTO users VALUES (2,'admin','admin123','admin','CTF{admin_secret}')")
        con.execute("INSERT OR IGNORE INTO items VALUES (1,'Widget','A fine widget'),(2,'Gadget','A fine gadget')")
        con.commit()
        return con

def q(con, sql, params=None):
    """Run a query, translating ? placeholders for Postgres."""
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

@app.route("/")
def index():
    challenges = [
        ("c1", "Hidden Page", "Directory Discovery", "Easy", 100),
        ("c2", "Cookie Monster", "Cookies & Sessions", "Easy", 100),
        ("c3", "Encoded Login", "Encoding", "Easy", 100),
        ("c4", "Inspect Me", "Source Code Analysis", "Easy", 100),
        ("c5", "Weak Password", "Authentication", "Easy", 100),
        ("c6", "Login Bypass", "SQL Injection", "Medium", 200),
        ("c7", "Search Box", "SQL Injection", "Medium", 200),
        ("c8", "Comment Box", "Cross-Site Scripting", "Medium", 200),
        ("c9", "User Profile", "IDOR", "Medium", 200),
        ("c10", "Debug Mode", "Information Disclosure", "Medium", 200),
        ("c11", "File Upload", "File Upload Security", "Advanced", 300),
        ("c12", "Admin Panel", "Authentication Bypass", "Advanced", 300),
        ("c13", "Blind SQLi", "Blind SQL Injection", "Hard", 400),
        ("c14", "SSRF Lab", "Server-Side Request Forgery", "Hard", 400),
        ("c15", "JWT Trap", "JWT Security", "Hard", 400),
    ]
    rows = "".join(f"<tr><td>{i+1}</td><td><a href='/{k}'>{n}</a></td><td>{c}</td><td>{d}</td><td>{p}</td></tr>" for i,(k,n,c,d,p) in enumerate(challenges))
    return page("HackQuest CTF - Web Security", f"""
    <p>Solve the challenges. Find the flags. Join your team to record scores.</p>
    <p><a href="/join">Join Team</a> | <a href="/leaderboard">Live Scoreboard</a></p>
    <table><tr><th>#</th><th>Challenge</th><th>Concept</th><th>Difficulty</th><th>Points</th></tr>{rows}</table>
    """)

@app.route("/join", methods=["GET","POST"])
def join():
    if request.method == "POST":
        team = request.form.get("team","").strip() or "Anonymous"
        session["team"] = team
        con = get_db()
        q(con, "INSERT INTO teams (team) VALUES (?) ON CONFLICT DO NOTHING", (team,))
        commit(con)
        con.close()
        resp = make_response(page("Joined", f"<p>Welcome <b>{team}</b>! You are on the scoreboard. Start solving: <a href='/'>challenges</a></p>"))
        resp.set_cookie("hackquest_team", team, max_age=30*24*3600)
        return resp
    return page("Join Team", "<form method='post'><input name='team' placeholder='Team name'><button>Join</button></form>")

@app.route("/leaderboard")
def leaderboard():
    con = get_db()
    rows = q(con, """
        SELECT t.team,
               COUNT(s.challenge) AS solves,
               COALESCE(SUM(s.points),0) AS score
        FROM teams t
        LEFT JOIN scores s ON s.team = t.team
        GROUP BY t.team
        ORDER BY score DESC, MIN(COALESCE(s.at, t.at)) ASC
    """).fetchall()
    con.close()
    team = get_team()
    body = "<table><tr><th>Rank</th><th>Team</th><th>Solves</th><th>Score</th></tr>"
    for i,(t,s,sc) in enumerate(rows,1):
        mark = " 👈" if team and t == team else ""
        body += f"<tr><td>{i}</td><td>{t}{mark}</td><td>{s}</td><td>{sc}</td></tr>"
    body += "</table>" if rows else "<p>No teams yet. <a href='/join'>Join first!</a></p>"
    if not team:
        body += "<p><b>You haven't joined a team yet.</b> <a href='/join'>Join a team</a> to appear on the scoreboard.</p>"
    else:
        body += f"<p>You are playing as <b>{team}</b>. <a href='/join'>Switch team</a></p>"
    return page("Live Scoreboard", body)

def record_score(challenge, points):
    team = get_team()
    if not team:
        return
    try:
        con = get_db()
        q(con, "INSERT INTO teams (team) VALUES (?) ON CONFLICT DO NOTHING", (team,))
        exists = q(con, "SELECT 1 FROM scores WHERE team=? AND challenge=?", (team, challenge)).fetchone()
        if not exists:
            q(con, "INSERT INTO scores (team,challenge,points) VALUES (?,?,?)", (team, challenge, points))
        commit(con)
        con.close()
    except Exception as e:
        app.logger.error(f"record_score failed: {e}")

@app.route("/admin")
def admin_panel():
    """Admin panel: view standings, download CSV, clear leaderboard between rounds."""
    if request.args.get("token") != ADMIN_TOKEN:
        return page("Admin", "<p>Invalid or missing token. Usage: /admin?token=YOUR_TOKEN</p>"), 403
    con = get_db()
    rows = q(con, """
        SELECT t.team, COUNT(s.challenge) AS solves, COALESCE(SUM(s.points),0) AS score
        FROM teams t LEFT JOIN scores s ON s.team = t.team
        GROUP BY t.team ORDER BY score DESC
    """).fetchall()
    con.close()
    body = "<table><tr><th>Rank</th><th>Team</th><th>Solves</th><th>Score</th></tr>"
    for i,(t,s,sc) in enumerate(rows,1):
        body += f"<tr><td>{i}</td><td>{t}</td><td>{s}</td><td>{sc}</td></tr>"
    body += "</table>" if rows else "<p>No teams yet.</p>"
    body += """
    <hr>
    <h3>Round Management</h3>
    <p>After each round of 4 challenges, clear the leaderboard to start the next round fresh:</p>
    <button onclick="if(confirm('Clear ALL teams and scores? This cannot be undone.')){window.location='/admin/reset?token=TOKEN'}">🗑 Clear Leaderboard (start next round)</button>
    <p><a href='/admin/export?token=TOKEN'>⬇ Download current standings (CSV)</a></p>
    <p style='color:var(--muted);font-size:.85rem'><i>Tip: Download the CSV before clearing to keep a record of each round.</i></p>
    """.replace("TOKEN", ADMIN_TOKEN)
    return page("Admin Panel", body)

@app.route("/admin/export")
def admin_export():
    """Download current standings as CSV. Requires ?token=<ADMIN_TOKEN>."""
    if request.args.get("token") != ADMIN_TOKEN:
        return "Invalid token", 403
    con = get_db()
    rows = q(con, """
        SELECT t.team, COUNT(s.challenge) AS solves, COALESCE(SUM(s.points),0) AS score
        FROM teams t LEFT JOIN scores s ON s.team = t.team
        GROUP BY t.team ORDER BY score DESC
    """).fetchall()
    con.close()
    import csv, io
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Rank", "Team", "Solves", "Score"])
    for i,(t,s,sc) in enumerate(rows,1):
        w.writerow([i, t, s, sc])
    return buf.getvalue(), 200, {"Content-Type": "text/csv", "Content-Disposition": "attachment; filename=hackquest_standings.csv"}

@app.route("/admin/reset")
def admin_reset():
    """Clear all teams and scores. Requires ?token=<ADMIN_TOKEN>."""
    if request.args.get("token") != ADMIN_TOKEN:
        return page("Admin", "<p>Invalid token.</p>"), 403
    con = get_db()
    if IS_PG:
        con.cursor().execute("DELETE FROM scores")
        con.cursor().execute("DELETE FROM teams")
    else:
        con.execute("DELETE FROM scores")
        con.execute("DELETE FROM teams")
    commit(con)
    con.close()
    return page("Admin Reset", "<div class='flag'>Leaderboard cleared. All teams and scores removed.</div><p><a href='/admin?token=TOKEN'>Back to admin panel</a> | <a href='/leaderboard'>View scoreboard</a></p>".replace("TOKEN", ADMIN_TOKEN))

# ---------- 1. Hidden Page ----------
@app.route("/c1")
def c1():
    return page("Hidden Page", """
    <p>There's a hidden page somewhere. Check common discovery files.</p>
    <p>Hint: try <a href="/robots.txt">/robots.txt</a></p>
    """)

@app.route("/robots.txt")
def robots():
    return "User-agent: *\nDisallow: /secret-admin-panel\n"

@app.route("/secret-admin-panel")
def secret_admin_panel():
    record_score("c1", 100)
    return page("Found!", "<div class='flag'>CTF{hidden_directory_found}</div>")

# ---------- 2. Cookie Monster ----------
@app.route("/c2")
def c2():
    role = request.cookies.get("role","guest")
    if role == "admin":
        record_score("c2", 100)
        return page("Cookie Monster", "<div class='flag'>CTF{cookie_monster_admin}</div>")
    return page("Cookie Monster", f"""
    <p>Your role cookie: <code>role={role}</code></p>
    <p>Only admins see the flag. Try editing your cookies in the browser dev tools (F12 &rarr; Application &rarr; Cookies).</p>
    """)

# ---------- 3. Encoded Login ----------
@app.route("/c3", methods=["GET","POST"])
def c3():
    msg = ""
    if request.method == "POST":
        u, p = request.form.get("u",""), request.form.get("p","")
        if u == "admin" and p == "c0d3x_enc0ded":
            record_score("c3", 100)
            msg = "<div class='flag'>CTF{encoding_master}</div>"
        else:
            msg = "<p>Login failed.</p>"
    creds = base64.b64encode(b"admin:c0d3x_enc0ded").decode()
    return page("Encoded Login", f"""
    <p>Login credentials are hidden in the page source.</p>
    <!-- credentials: {creds} -->
    <form method='post'><input name='u' placeholder='username'><input name='p' placeholder='password'><button>Login</button></form>{msg}
    """)

# ---------- 4. Inspect Me ----------
@app.route("/c4")
def c4():
    return page("Inspect Me", """
    <p>The flag is closer than you think.</p>
    <!-- CTF{inspect_the_source} -->
    """)

# ---------- 5. Weak Password ----------
@app.route("/c5", methods=["GET","POST"])
def c5():
    msg = ""
    if request.method == "POST":
        if request.form.get("username") == "admin" and request.form.get("password") == "admin123":
            record_score("c5", 100)
            msg = "<div class='flag'>CTF{weak_passwords_fall}</div>"
        else:
            msg = "<p>Try harder. Common passwords...</p>"
    return page("Weak Password", f"""
    <form method='post'><input name='username' placeholder='username'><input name='password' placeholder='password'><button>Login</button></form>{msg}
    """)

# ---------- 6. Login Bypass SQLi ----------
@app.route("/c6", methods=["GET","POST"])
def c6():
    msg = ""
    if request.method == "POST":
        u, p = request.form.get("u",""), request.form.get("p","")
        con = get_db()
        try:
            row = q(con, f"SELECT * FROM users WHERE name='{u}' AND password='{p}'").fetchone()
            if row:
                record_score("c6", 200)
                msg = "<div class='flag'>CTF{sql_injection_bypass}</div>"
            else:
                msg = f"<p>No user {u}.</p>"
        except Exception as e:
            msg = f"<p>Error: {e}</p>"
        con.close()
    return page("Login Bypass", f"""
    <p>Try to log in without knowing the password.</p>
    <form method='post'><input name='u' placeholder='username'><input name='p' placeholder='password'><button>Login</button></form>{msg}
    """)

# ---------- 7. Search Box SQLi ----------
@app.route("/c7")
def c7():
    qstr = request.args.get("q","")
    out = ""
    if qstr:
        con = get_db()
        try:
            rows = q(con, f"SELECT name, description FROM items WHERE name LIKE '%{qstr}%'").fetchall()
            out = "<ul>" + "".join(f"<li>{n}: {d}</li>" for n,d in rows) + "</ul>"
            if "'" in qstr:
                record_score("c7", 200)
                out += "<div class='flag'>CTF{union_based_sqli}</div>"
        except Exception as e:
            out = f"<p>Error: {e}</p>"
        con.close()
    return page("Search Box", f"""
    <form><input name='q' placeholder='search items'><button>Search</button></form>{out}
    """)

# ---------- 8. Comment Box XSS ----------
@app.route("/c8", methods=["GET","POST"])
def c8():
    con = get_db()
    if request.method == "POST":
        q(con, "INSERT INTO comments (text) VALUES (?)", (request.form.get("text",""),))
        commit(con)
    rows = q(con, "SELECT text FROM comments").fetchall()
    con.close()
    comments = "".join(f"<div class='comment'>{t}</div>" for (t,) in rows)
    flag = ""
    if any("<script" in t.lower() for (t,) in rows):
        record_score("c8", 200)
        flag = "<div class='flag'>CTF{xss_popped_alert}</div><script>alert('XSS!')</script>"
    return page("Comment Box", f"""
    <form method='post'><input name='text' placeholder='comment'><button>Post</button></form>
    {comments}{flag}
    """)

# ---------- 9. User Profile IDOR ----------
@app.route("/c9")
def c9():
    uid = request.args.get("id","1")
    if uid == "1":
        body = "<p><b>alice</b> - email: alice@hackquest.dev</p><p>Try <a href='/c9?id=2'>id=2</a></p>"
    elif uid == "2":
        record_score("c9", 200)
        body = "<p><b>admin</b> - email: admin@hackquest.dev</p><div class='flag'>CTF{idor_profile_accessed}</div>"
    else:
        body = "<p>No such profile.</p>"
    return page("User Profile", body)

# ---------- 10. Debug Mode ----------
@app.route("/c10")
def c10():
    if request.args.get("debug","").lower() in ("1","true","on"):
        record_score("c10", 200)
        return page("Debug Mode", "<pre>DEBUG MODE ENABLED\nDB_PASS=s3cr3t\nFLAG=CTF{debug_mode_disclosed}</pre>")
    return page("Debug Mode", "<p>Production mode. No debug info. (Hint: ?debug=true)</p>")

# ---------- 11. File Upload ----------
@app.route("/c11", methods=["GET","POST"])
def c11():
    msg = ""
    if request.method == "POST" and "f" in request.files:
        f = request.files["f"]
        filename = f.filename or ""
        f.save(os.path.join(UPLOAD_DIR, filename))
        content = open(os.path.join(UPLOAD_DIR, filename), "rb").read(200).decode(errors="ignore")
        if filename.lower().endswith((".php",".jsp",".exe",".sh")) or "<?php" in content:
            record_score("c11", 300)
            msg = "<div class='flag'>CTF{arbitrary_file_upload}</div>"
        else:
            msg = f"<p>Uploaded {filename} as a 'safe' file.</p>"
    return page("File Upload", f"""
    <form method='post' enctype='multipart/form-data'><input type='file' name='f'><button>Upload</button></form>{msg}
    <p>We only accept images... supposedly. Try a .php file.</p>
    """)

# ---------- 12. Admin Panel Auth Bypass ----------
@app.route("/c12")
def c12():
    if request.headers.get("X-Admin-Access","").lower() == "true" or request.args.get("admin") == "1":
        record_score("c12", 300)
        return page("Admin Panel", "<div class='flag'>CTF{admin_header_bypass}</div>")
    return page("Admin Panel", "<p>Admins only. <!-- Try adding header X-Admin-Access: true, or visit ?admin=1 --></p>")

# ---------- 13. Blind SQLi ----------
@app.route("/c13")
def c13():
    uid = request.args.get("id","")
    con = get_db()
    exists = False
    if uid:
        try:
            row = q(con, f"SELECT id FROM users WHERE id={uid}").fetchone()
            exists = bool(row)
        except Exception:
            exists = False
    con.close()
    body = f"<p>User {'EXISTS' if exists else 'does not exist'} (id={uid or '?'})</p>"
    guess = request.args.get("secret","")
    if guess == "CTF{blind_sqli_hunter}":
        record_score("c13", 400)
        body += "<div class='flag'>CTF{blind_sqli_hunter}</div>"
    return page("Blind SQLi", body + "<p>Boolean oracle only. Extract alice's secret from the users table, then submit ?secret=...</p>")

# ---------- 14. SSRF Lab ----------
@app.route("/c14")
def c14():
    url = request.args.get("url","")
    out = ""
    if url:
        try:
            import urllib.request
            out = "<pre>" + urllib.request.urlopen(url, timeout=5).read(500).decode(errors="ignore") + "</pre>"
            if "CTF{ssrf_internal_reached}" in out:
                record_score("c14", 400)
        except Exception as e:
            out = f"<p>Error: {e}</p>"
    return page("SSRF Lab", f"""
    <form><input name='url' placeholder='http://'><button>Fetch</button></form>{out}
    <p>Try fetching the internal endpoint: <code>http://127.0.0.1:{PORT}/internal/flag</code></p>
    """)

@app.route("/internal/flag")
def internal_flag():
    ua = request.headers.get("User-Agent","")
    host = request.headers.get("Host","")
    if "python-urllib" in ua.lower() or host.startswith("127.0.0.1") or host.startswith("localhost"):
        return "CTF{ssrf_internal_reached}"
    return "forbidden"

# ---------- 15. JWT Trap ----------
SECRET = "hackquest_secret_key"
def b64(d): return base64.urlsafe_b64encode(d).rstrip(b"=").decode()

@app.route("/c15")
def c15():
    tok = request.args.get("token")
    msg = ""
    if not tok:
        payload = b64(json.dumps({"alg":"HS256","typ":"JWT"}).encode())
        body = b64(json.dumps({"user":"guest","role":"user"}).encode())
        sig = b64(hmac.new(SECRET.encode(), f"{payload}.{body}".encode(), hashlib.sha256).digest())
        msg = f"<p>Your token: <code>{payload}.{body}.{sig}</code></p><p>Goal: become admin. (Try alg:none)</p>"
    else:
        try:
            h, b, s = tok.split(".")
            header = json.loads(base64.urlsafe_b64decode(h + "=" * (-len(h) % 4)))
            data = json.loads(base64.urlsafe_b64decode(b + "=" * (-len(b) % 4)))
            if header.get("alg","").lower() == "none":
                ok = True
            else:
                ok = s == b64(hmac.new(SECRET.encode(), f"{h}.{b}".encode(), hashlib.sha256).digest())
            if ok and data.get("role") == "admin":
                record_score("c15", 400)
                msg = "<div class='flag'>CTF{jwt_none_algorithm}</div>"
            elif ok:
                msg = f"<p>Welcome {data.get('user')} (role: {data.get('role')})</p>"
            else:
                msg = "<p>Invalid signature.</p>"
        except Exception as e:
            msg = f"<p>Bad token: {e}</p>"
    return page("JWT Trap", msg + "<form><input name='token' placeholder='JWT'><button>Verify</button></form>")

if __name__ == "__main__":
    get_db().close()
    app.run(host="0.0.0.0", debug=True, port=int(PORT))
