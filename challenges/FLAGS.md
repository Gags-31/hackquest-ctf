# HackQuest CTF — Web Security Challenge Lab
15 web security challenges. Run: `python app.py` -> http://localhost:5000

## Challenges
| # | Challenge | Concept | Difficulty | Points |
|---|---|---|---|---|
| 1 | Hidden Page | Directory Discovery | Easy | 100 |
| 2 | Cookie Monster | Cookies & Sessions | Easy | 100 |
| 3 | Encoded Login | Encoding | Easy | 100 |
| 4 | Inspect Me | Source Code Analysis | Easy | 100 |
| 5 | Weak Password | Authentication | Easy | 100 |
| 6 | Login Bypass | SQL Injection | Medium | 200 |
| 7 | Search Box | SQL Injection | Medium | 200 |
| 8 | Comment Box | Cross-Site Scripting | Medium | 200 |
| 9 | User Profile | IDOR | Medium | 200 |
| 10 | Debug Mode | Information Disclosure | Medium | 200 |
| 11 | File Upload | File Upload Security | Advanced | 300 |
| 12 | Admin Panel | Authentication Bypass | Advanced | 300 |
| 13 | Blind SQLi | Blind SQL Injection | Hard | 400 |
| 14 | SSRF Lab | Server-Side Request Forgery | Hard | 400 |
| 15 | JWT Trap | JWT Security | Hard | 400 |

**Max Score: 3,000**

## Flags & Solutions (organizers only)
| # | Flag | Solution |
|---|---|---|
| 1 | `CTF{hidden_directory_found}` | Visit `/robots.txt` then `/secret-admin-panel` |
| 2 | `CTF{cookie_monster_admin}` | Set cookie `role=admin` |
| 3 | `CTF{encoding_master}` | View source for base64 `admin:c0d3x_enc0ded` |
| 4 | `CTF{inspect_the_source}` | View page source |
| 5 | `CTF{weak_passwords_fall}` | Login `admin`/`admin123` |
| 6 | `CTF{sql_injection_bypass}` | Username: `' OR '1'='1` |
| 7 | `CTF{union_based_sqli}` | Search with `'` to trigger injection |
| 8 | `CTF{xss_popped_alert}` | Post comment with `<script>alert(1)</script>` |
| 9 | `CTF{idor_profile_accessed}` | Change `?id=1` to `?id=2` |
| 10 | `CTF{debug_mode_disclosed}` | Add `?debug=true` |
| 11 | `CTF{arbitrary_file_upload}` | Upload a `.php` file |
| 12 | `CTF{admin_header_bypass}` | Add header `X-Admin-Access: true` |
| 13 | `CTF{blind_sqli_hunter}` | Boolean-based extraction, then `?secret=CTF{blind_sqli_hunter}` |
| 14 | `CTF{ssrf_internal_reached}` | `/c14?url=http://127.0.0.1:5000/internal/flag` |
| 15 | `CTF{jwt_none_algorithm}` | Forge JWT with `alg:none` and `role:admin` |

## Deploy
- Local: `pip install flask` then `python app.py`
- Render: use `render.yaml` (build: `pip install -r requirements.txt`, start: `cd challenges && gunicorn app:app`)
