"""HackQuest CTF — 15 coding-contest style challenges (Flask).
Run: python app.py  ->  http://127.0.0.1:5000"""
import hashlib
import hmac
import os
from flask import Flask, request, render_template_string, session

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "hackquest_dev_secret")
DB = os.path.join(os.path.dirname(__file__), "ctf.db")

import sqlite3
def get_db():
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS scores (team TEXT, challenge TEXT, points INTEGER, at TEXT DEFAULT (datetime('now')))")
    con.commit()
    return con

POINTS = {"/c1":100,"/c2":100,"/c3":100,"/c4":100,"/c5":100,"/c6":200,"/c7":200,"/c8":200,"/c9":200,"/c10":200,"/c11":300,"/c12":300,"/c13":300,"/c14":400,"/c15":400}

PAGE = """<!DOCTYPE html><html><head><title>{{title}}</title>
<style>body{font-family:Consolas,monospace;background:#0d1117;color:#e6edf3;max-width:820px;margin:40px auto;padding:0 16px}
h2{color:#2ea043}input{padding:8px;width:60%;background:#161b22;border:1px solid #30363d;color:#e6edf3;border-radius:6px}
button{padding:8px 18px;background:#238636;color:#fff;border:none;cursor:pointer;border-radius:6px}
pre{background:#161b22;padding:12px;border-radius:6px;overflow-x:auto;white-space:pre-wrap}
.flag{background:#238636;padding:12px;border-radius:6px;margin:12px 0;font-size:1.1em}
a{color:#58a6ff}code{color:#f0883e}</style></head>
<body><h2>{{title}}</h2>{{body|safe}}<p><a href="/">&larr; all challenges</a></p></body></html>"""

def page(title, body):
    return render_template_string(PAGE, title=title, body=body)

def challenge(title, desc, code, answer_fn, flag, hint=""):
    msg = ""
    if request.method == "POST":
        guess = request.form.get("answer", "").strip()
        if answer_fn(guess):
            team = session.get("team")
            if team:
                con = get_db()
                exists = con.execute("SELECT 1 FROM scores WHERE team=? AND challenge=?", (team, request.path)).fetchone()
                if not exists:
                    con.execute("INSERT INTO scores (team, challenge, points) VALUES (?,?,?)", (team, request.path, POINTS.get(request.path, 100)))
                    con.commit()
                con.close()
                msg = f"<div class='flag'>✅ Correct! {flag}</div>"
            else:
                msg = f"<div class='flag'>✅ Correct! {flag}</div><p>⚠️ Log in with your team name to record score: <a href='/join'>join</a></p>"
        else:
            msg = "<p>✕ Incorrect answer. Try again.</p>"
    return page(title, f"<p>{desc}</p><pre>{code}</pre>"
                + (f"<p><i>Hint: {hint}</i></p>" if hint else "")
                + f'<form method="post"><input name="answer" placeholder="your answer" autocomplete="off"><button>Submit</button></form>{msg}')

CHALLENGES = []
def reg(route):
    def wrap(fn):
        CHALLENGES.append((fn.__name__[1:], (fn.__doc__ or "").strip(), route))
        app.route(route, methods=["GET", "POST"])(fn)
        return fn
    return wrap

@app.route("/join", methods=["GET", "POST"])
def join():
    if request.method == "POST":
        session["team"] = request.form.get("team", "").strip() or "Anonymous"
        return page("Joined", f"<p>Welcome, <b>{session['team']}</b>! Scores will be recorded. <a href='/'>Start</a></p>")
    return page("Join Team", '<form method="post"><input name="team" placeholder="Team name"><button>Join</button></form>')

@app.route("/leaderboard")
def leaderboard():
    con = get_db()
    rows = con.execute("SELECT team, COUNT(*) AS solves, SUM(points) AS score FROM scores GROUP BY team ORDER BY score DESC, MIN(at) ASC").fetchall()
    con.close()
    body = "<table border='1' cellpadding='8' cellspacing='0'><tr><th>Rank</th><th>Team</th><th>Solves</th><th>Score</th></tr>"
    for i, (t, s, sc) in enumerate(rows, 1):
        body += f"<tr><td>{i}</td><td>{t}</td><td>{s}</td><td>{sc}</td></tr>"
    body += "</table>" if rows else "<p>No solves yet. Be the first!</p>"
    return page("Live Scoreboard", body + "<p><a href='/'>&larr; challenges</a> · <a href='/join'>join/switch team</a></p>")

@app.route("/")
def index():
    items = "".join(f'<li><a href="{r}">{n}</a> — {d}</li>' for n, d, r in CHALLENGES)
    return page("HackQuest CTF — Coding Contest", f"<p>Solve the coding problems and submit answers to capture flags. <a href='/join'>Join a team</a> · <a href='/leaderboard'>Live scoreboard</a></p><ol>{items}</ol>")

# ---------- Easy (100) ----------
@reg("/c1")
def c1():
    """FizzBuzz Sum"""
    return challenge("FizzBuzz Sum", "For all integers from 1 to 100 inclusive, if the number is divisible by 3 or 5, add it to the total. What is the total?",
        "total = 0\nfor n in range(1, 101):\n    if n % 3 == 0 or n % 5 == 0:\n        total += n\nprint(total)",
        lambda a: a == "2418", "CTF{fizzbuzz_sum_2418}", "Write a quick script to compute it.")

@reg("/c2")
def c2():
    """Reverse Twist"""
    return challenge("Reverse Twist",
        "Reverse the following string and then take the first 10 characters.",
        "s = 'n6yw2oYXq7semeT'",
        lambda a: a == "Temes7qXYo", "CTF{twist_reversed}", "s[::-1][:10]")

@reg("/c3")
def c3():
    """Caesar Shift"""
    return challenge("Caesar Shift", "The message was encrypted with a Caesar cipher (shift +3). Decode it.",
        "ciphertext = 'fdswxuh_wkh_iodj'",
        lambda a: a.lower() == "capture_the_flag", "CTF{caesar_decoded}", "Shift each letter back by 3.")

@reg("/c4")
def c4():
    """Base64 Quest"""
    import base64
    enc = base64.b64encode(b"CTF{base64_is_not_encryption}").decode()
    return challenge("Base64 Quest", "Decode the Base64 string below. Submit the decoded text as your answer.",
        f"data = '{enc}'",
        lambda a: a == "CTF{base64_is_not_encryption}", "CTF{base64_is_not_encryption}", "Use base64.b64decode().")

@reg("/c5")
def c5():
    """Vowel Counter"""
    return challenge("Vowel Counter", "How many vowels (a, e, i, o, u, case-insensitive) are in the string?",
        "s = 'AsynchronouslyOptimizeVulnerabilities'",
        lambda a: a == "15", "CTF{vowel_counter}", "Count carefully.")

# ---------- Medium (200) ----------
@reg("/c6")
def c6():
    """Fibonacci Target"""
    return challenge("Fibonacci Target", "Using F(0)=0 and F(1)=1, what is F(30)?",
        "# F(0)=0, F(1)=1\n# F(n) = F(n-1) + F(n-2)",
        lambda a: a == "832040", "CTF{fib_30}", "Iterative loop is fastest.")

@reg("/c7")
def c7():
    """Missing Number"""
    return challenge("Missing Number", "The list contains every number from 1 to 20 except one. Which number is missing?",
        "nums = [1,2,3,4,5,6,7,8,9,10,11,12,13,15,16,17,18,19,20]",
        lambda a: a == "14", "CTF{missing_14}", "Compare to 1..20.")

@reg("/c8")
def c8():
    """Roman Decoder"""
    return challenge("Roman Decoder", "Convert the Roman numeral to an integer.",
        "numeral = 'MCMXCIV'",
        lambda a: a == "1994", "CTF{mcmxiv_1994}", "M=1000, CM=900, XC=90, IV=4.")

@reg("/c9")
def c9():
    """Binary Bridge"""
    return challenge("Binary Bridge", "What is the decimal value of this binary number?",
        "n = '0b1011011011'",
        lambda a: a == "731", "CTF{binary_731}", "int(n, 2).")

@reg("/c10")
def c10():
    """Palindrome Gate"""
    return challenge("Palindrome Gate", "Which word, when its characters are reversed, does NOT equal itself?",
        "words = ['level', 'radar', 'civic', 'kayak', 'hacker']",
        lambda a: a.lower() == "hacker", "CTF{hacker_not_palindrome}", "Check each reversed.")

# ---------- Advanced (300) ----------
@reg("/c11")
def c11():
    """Prime Hunter"""
    return challenge("Prime Hunter", "What is the 50th prime number? (2 is the 1st)",
        "# primes: 2, 3, 5, 7, 11, ...",
        lambda a: a == "229", "CTF{prime_50}", "Sieve of Eratosthenes.")

@reg("/c12")
def c12():
    """XOR Cipher"""
    import binascii
    ct = bytes(b ^ 0x42 for b in b"CTF{xor_is_symmetric}")
    return challenge("XOR Cipher", "Every byte of the message was XORed with 0x42 ('B'). Decrypt the hex and submit the plaintext.",
        f"ciphertext_hex = '{ct.hex()}'\nkey = 0x42",
        lambda a: a == "CTF{xor_is_symmetric}", "CTF{xor_is_symmetric}", "bytes(b ^ 0x42 for b in ...)")

@reg("/c13")
def c13():
    """Two Sum"""
    return challenge("Two Sum", "Return the 0-indexed pair of indices whose values add up to target. Format: i,j (smaller index first).",
        "nums = [2, 7, 11, 15, 3, 6]\ntarget = 9",
        lambda a: a.replace(" ", "") == "0,1", "CTF{two_sum_0_1}", "Only one valid pair.")

# ---------- Hard (400) ----------
@reg("/c14")
def c14():
    """Hash Triangle"""
    h = hashlib.sha256(b"hackquest").hexdigest()
    return challenge("Hash Triangle", "Compute SHA-256 of the UTF-8 string 'hackquest'. What is the first 8 hex characters of the digest?",
        "import hashlib\nhashlib.sha256('hackquest'.encode()).hexdigest()",
        lambda a: a.lower() == h[:8], "CTF{hash_prefix}", "Use hashlib.")

@reg("/c15")
def c15():
    import base64, json as j
    payload = "fyZ5d2l2Jj4mZWhxbXImMCZ2c3BpJj4mdnNzeCbCgQ"
    return challenge("Capstone Logic", "A JSON message was processed in two steps: (1) each character's ASCII code was shifted +4, (2) the result was base64url-encoded. Decrypt it and submit the original JSON string (exactly).",
        f"data = '{payload}'",
        lambda a: a == '{"user":"admin","role":"root"}', "CTF{capstone_decoded}",
        "Reverse order: base64url decode, then shift each char back by 4.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=int(os.environ.get("PORT", 5000)))
