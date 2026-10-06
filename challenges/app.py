"""HackQuest CTF — 15 web security challenges in one Flask app.
Run: python app.py  ->  http://127.0.0.1:5000"""
import base64
import hashlib
import hmac
import json
import os
import sqlite3
import urllib.request
from io import BytesIO

from flask import Flask, request, make_response, redirect, jsonify, render_template_string, send_from_directory

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
DB = os.path.join(os.path.dirname(__file__), "ctf.db")

PAGE = """<!DOCTYPE html><html><head><title>{{title}}</title>
<style>body{font-family:Consolas,monospace;background:#0d1117;color:#e6edf3;max-width:800px;margin:40px auto}
a{color:#58a6ff}input{padding:6px;margin:4px}button{padding:6px 14px;background:#238636;color:#fff;border:none;cursor:pointer}
.flag{background:#238636;padding:10px;border-radius:6px;margin:10px 0}</style></head>
<body><h2>{{title}}</h2>{{body|safe}}<p><a href="/">&larr; all challenges</a></p></body></html>"""

def page(title, body):
    return render_template_string(PAGE, title=title, body=body)

def get_db():
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, secret TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, name TEXT, desc TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS comments (id INTEGER PRIMARY KEY, text TEXT)")
    con.execute("INSERT OR IGNORE INTO users VALUES (1,'alice','CTF{blind_sqli_hunter}')")
    con.execute("INSERT OR IGNORE INTO items VALUES (1,'Widget','A fine widget'),(2,'Gadget','A fine gadget')")
    con.commit()
    return con

@app.route("/")
def index():
    items = "".join(f'<li>{i}. <a href="{u}">{n}</a> — {d}</li>' for i, n, u, d in [
        (1, "Hidden Page", "/c1", "directory discovery"),
        (2, "Cookie Monster", "/c2", "cookies & sessions"),
        (3, "Encoded Login", "/c3", "encoding"),
        (4, "Inspect Me", "/c4", "source code analysis"),
        (5, "Weak Password", "/c5", "authentication"),
        (6, "Login Bypass", "/c6", "SQL injection"),
        (7, "Search Box", "/c7", "SQL injection"),
        (8, "Comment Box", "/c8", "XSS"),
        (9, "User Profile", "/c9", "IDOR"),
        (10, "Debug Mode", "/c10", "info disclosure"),
        (11, "File Upload", "/c11", "file upload"),
        (12, "Admin Panel", "/c12", "auth bypass"),
        (13, "Blind SQLi", "/c13", "blind SQL injection"),
        (14, "SSRF Lab", "/c14", "server-side request forgery"),
        (15, "JWT Trap", "/c15", "JWT security"),
    ])
    return page("HackQuest CTF Challenges", f"<ol>{items}</ol><p><a href='/robots.txt'>robots.txt</a> hints at challenge 1.")

# ---------- 1. Hidden Page ----------
@app.route("/robots.txt")
def robots():
    return app.response_class("User-agent: *\nDisallow: /hidden-secret-page\n", mimetype="text/plain")

@app.route("/c1")
def c1():
    return page("Hidden Page", "<p>Nothing to see here. Check common discovery files like robots.txt...</p>")

@app.route("/hidden-secret-page")
def hidden():
    return page("Found it!", "<div class='flag'>CTF{hidden_directory_found}</div>")

# ---------- 2. Cookie Monster ----------
@app.route("/c2")
def c2():
    role = request.cookies.get("role", "guest")
    body = f"<p>Your role cookie: <code>role={role}</code></p>"
    if role == "admin":
        body += "<div class='flag'>CTF{cookie_monster_admin}</div>"
    else:
        body += "<p>Only admins can see the flag.</p>"
    r = make_response(page("Cookie Monster", body))
    if "role" not in request.cookies:
        r.set_cookie("role", "guest")
    return r

# ---------- 3. Encoded Login ----------
@app.route("/c3")
def c3():
    msg = ""
    if request.method == "POST" or request.args.get("u"):
        u, p = request.values.get("u", ""), request.values.get("p", "")
        if u == "admin" and p == "c0d3x_enc0ded":
            msg = "<div class='flag'>CTF{encoding_master}</div>"
        else:
            msg = "<p>Login failed.</p>"
    creds = base64.b64encode(b"admin:c0d3x_enc0ded").decode()
    return page("Encoded Login", f"""<p>Credentials are safe... somewhere in the page source. Nothing suspicious here:</p>
    <!-- credentials: {creds} -->
    <form method="post"><input name="u" placeholder="user"><input name="p" placeholder="pass"><button>Login</button></form>{msg}""")

# ---------- 4. Inspect Me ----------
@app.route("/c4")
def c4():
    return page("Inspect Me", """<p>The flag is closer than you think.</p>
    <!-- CTF{inspect_the_source} -->""")

# ---------- 5. Weak Password ----------
@app.route("/c5", methods=["GET", "POST"])
def c5():
    msg = ""
    if request.method == "POST":
        if request.form.get("username") == "admin" and request.form.get("password") == "admin123":
            msg = "<div class='flag'>CTF{weak_passwords_fall}</div>"
        else:
            msg = "<p>Try harder. Common passwords...</p>"
    return page("Weak Password", f'<form method="post"><input name="username" placeholder="username"><input name="password" placeholder="password"><button>Login</button></form>{msg}')

# ---------- 6. Login Bypass SQLi ----------
@app.route("/c6", methods=["GET", "POST"])
def c6():
    msg = ""
    if request.method == "POST":
        u, p = request.form.get("u", ""), request.form.get("p", "")
        con = get_db()
        try:
            row = con.execute(f"SELECT * FROM users WHERE name='{u}' AND secret='{p}'").fetchone()
            if row or "' or " in u.lower() or "' or " in p.lower() or '" or ' in u.lower():
                msg = "<div class='flag'>CTF{sql_injection_bypass}</div>"
            else:
                msg = f"<p>No user {u}.</p>"
        except Exception as e:
            msg = f"<p>Error: {e}</p>"
        con.close()
    return page("Login Bypass", f'<form method="post"><input name="u" placeholder="user"><input name="p" placeholder="pass"><button>Go</button></form>{msg}')

# ---------- 7. Search Box SQLi ----------
@app.route("/c7")
def c7():
    q = request.args.get("q", "")
    out = ""
    if q:
        con = get_db()
        try:
            rows = con.execute(f"SELECT name, desc FROM items WHERE name LIKE '%{q}%'").fetchall()
            out = "<ul>" + "".join(f"<li>{n}: {d}</li>" for n, d in rows) + "</ul>"
            if "'" in q and ("union" in q.lower() or "or" in q.lower()):
                out += "<div class='flag'>CTF{union_based_sqli}</div>"
        except Exception as e:
            out = f"<p>Error: {e}</p>"
        con.close()
    return page("Search Box", f'<form><input name="q" placeholder="search items"><button>Search</button></form>{out}')

# ---------- 8. Comment Box XSS ----------
@app.route("/c8", methods=["GET", "POST"])
def c8():
    con = get_db()
    if request.method == "POST":
        con.execute("INSERT INTO comments (text) VALUES (?)", (request.form.get("text", ""),))
        con.commit()
    rows = con.execute("SELECT text FROM comments").fetchall()
    con.close()
    comments = "".join(f"<p>{t}</p>" for (t,) in rows)  # intentionally unescaped
    flag = ""
    if any("<script" in t.lower() for (t,) in rows):
        flag = "<div class='flag'>CTF{xss_popped_alert}</div><script>alert('XSS!')</script>"
    return page("Comment Box", f'<form method="post"><input name="text" placeholder="comment"><button>Post</button></form>{comments}{flag}')

# ---------- 9. IDOR ----------
@app.route("/c9")
def c9():
    uid = request.args.get("id", "1")
    if uid == "1":
        body = "<p><b>alice</b> — email: alice@hackquest.dev</p><p>Try <a href='/c9?id=2'>id=2</a>?</p>"
    elif uid == "2":
        body = "<p><b>admin</b> — email: admin@hackquest.dev</p><div class='flag'>CTF{idor_profile_accessed}</div>"
    else:
        body = "<p>No such profile.</p>"
    return page("User Profile", body)

# ---------- 10. Debug Mode ----------
@app.route("/c10")
def c10():
    if request.args.get("debug", "").lower() in ("1", "true", "on"):
        return page("Debug", "<pre>DEBUG MODE ENABLED\nDB_PASS=s3cr3t\nFLAG=CTF{debug_mode_disclosed}</pre>")
    return page("Debug Mode", "<p>Production mode. No debug info. (Hint: ?debug=true)</p>")

# ---------- 11. File Upload ----------
@app.route("/c11", methods=["GET", "POST"])
def c11():
    msg = ""
    if request.method == "POST" and "f" in request.files:
        f = request.files["f"]
        path = os.path.join(UPLOAD_DIR, f.filename)
        f.save(path)
        if f.filename.lower().endswith((".php", ".jsp", ".exe", ".sh")) or "<?php" in f.read(200).decode(errors="ignore"):
            msg = "<div class='flag'>CTF{arbitrary_file_upload}</div>"
        else:
            msg = f"<p>Uploaded {f.filename} as a 'safe' file.</p>"
    return page("File Upload", f'<form method="post" enctype="multipart/form-data"><input type="file" name="f"><button>Upload</button></form>{msg}<p>We only accept images... supposedly.</p>')

# ---------- 12. Admin Panel Auth Bypass ----------
@app.route("/c12")
def c12():
    if request.headers.get("X-Admin-Access", "").lower() == "true" or request.args.get("admin") == "1":
        return page("Admin Panel", "<div class='flag'>CTF{admin_header_bypass}</div>")
    return page("Admin Panel", "<p>Admins only. <!-- Try adding header X-Admin-Access: true --></p>")

# ---------- 13. Blind SQLi ----------
@app.route("/c13")
def c13():
    """Boolean-based blind SQLi. id=1 -> exists; payloads like 1' AND '1'='1 mirror true, '1'='2 -> missing.
    Flag unlocked by correctly guessing alice's secret length parity via SQL and submitting it."""
    uid = request.args.get("id", "")
    con = get_db()
    exists = False
    if uid:
        try:
            row = con.execute(f"SELECT id FROM users WHERE id={uid}").fetchone()
            exists = bool(row)
        except Exception:
            exists = False
    con.close()
    body = f"<p>User {'EXISTS ✔' if exists else 'does not exist ✘'} (id={uid or '?'})</p>"
    secret = b"CTF{blind_sqli_hunter}"
    guess = request.args.get("secret", "")
    if guess == secret.decode():
        body += "<div class='flag'>CTF{blind_sqli_hunter}</div>"
    return page("Blind SQLi", body + "<p>Boolean oracle only. Extract alice's secret from the users table, then submit ?secret=...</p>")

# ---------- 14. SSRF Lab ----------
@app.route("/c14")
def c14():
    url = request.args.get("url", "")
    out = ""
    if url:
        try:
            # vulnerable: fetches arbitrary URL, including internal endpoints
            out = "<pre>" + urllib.request.urlopen(url, timeout=3).read(500).decode(errors="ignore") + "</pre>"
        except Exception as e:
            out = f"<p>Error: {e}</p>"
    return page("SSRF Lab", f'<form><input name="url" placeholder="http://"><button>Fetch</button></form>{out}<p>Try http://127.0.0.1:5000/internal/flag</p>')

@app.route("/internal/flag")
def internal_flag():
    if request.remote_addr in ("127.0.0.1", "::1") and request.headers.get("X-Forwarded-For"):
        return "nope"
    # internal endpoint: trust-based gating by header simulating internal-only access
    if request.headers.get("Host", "").startswith("127.0.0.1"):
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
        payload = b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
        body = b64(json.dumps({"user": "guest", "role": "user"}).encode())
        sig = b64(hmac.new(SECRET.encode(), f"{payload}.{body}".encode(), hashlib.sha256).digest())
        msg = f"<p>Your token: <code>{payload}.{body}.{sig}</code></p><p>Goal: become admin. (Try alg:none)</p>"
    else:
        try:
            h, b, s = tok.split(".")
            header = json.loads(base64.urlsafe_b64decode(h + "=" * (-len(h) % 4)))
            data = json.loads(base64.urlsafe_b64decode(b + "=" * (-len(b) % 4)))
            if header.get("alg", "").lower() == "none":
                ok = True  # VULNERABLE: accepts alg:none
            else:
                ok = s == b64(hmac.new(SECRET.encode(), f"{h}.{b}".encode(), hashlib.sha256).digest())
            if ok and data.get("role") == "admin":
                msg = "<div class='flag'>CTF{jwt_none_algorithm}</div>"
            elif ok:
                msg = f"<p>Welcome {data.get('user')} (role: {data.get('role')})</p>"
            else:
                msg = "<p>Invalid signature.</p>"
        except Exception as e:
            msg = f"<p>Bad token: {e}</p>"
    return page("JWT Trap", msg + '<form><input name="token" placeholder="JWT"><button>Verify</button></form>')

if __name__ == "__main__":
    get_db().close()
    app.run(debug=True, port=5000)
