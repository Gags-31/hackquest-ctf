# HackQuest CTF — Flags & Solutions (for organizers/testing only)

| # | Challenge | Flag | Solution |
|---|---|---|---|
| 1 | Hidden Page | `CTF{hidden_directory_found}` | Check `/robots.txt` → visit `/hidden-secret-page` |
| 2 | Cookie Monster | `CTF{cookie_monster_admin}` | Set cookie `role=admin` (dev tools → Application → Cookies) |
| 3 | Encoded Login | `CTF{encoding_master}` | View page source: base64 `admin:c0d3x_enc0ded`, then login |
| 4 | Inspect Me | `CTF{inspect_the_source}` | View page source HTML comment |
| 5 | Weak Password | `CTF{weak_passwords_fall}` | Login `admin` / `admin123` |
| 6 | Login Bypass | `CTF{sql_injection_bypass}` | Username: `' OR '1'='1` — bypasses query |
| 7 | Search Box | `CTF{union_based_sqli}` | Search `' UNION SELECT` / `' OR '1'='1` |
| 8 | Comment Box | `CTF{xss_popped_alert}` | Post comment containing `<script>alert(1)</script>` |
| 9 | User Profile | `CTF{idor_profile_accessed}` | Change `?id=1` to `?id=2` |
| 10 | Debug Mode | `CTF{debug_mode_disclosed}` | Add `?debug=true` |
| 11 | File Upload | `CTF{arbitrary_file_upload}` | Upload a `.php` file or one containing `<?php` |
| 12 | Admin Panel | `CTF{admin_header_bypass}` | Add header `X-Admin-Access: true` or `?admin=1` |
| 13 | Blind SQLi | `CTF{blind_sqli_hunter}` | Boolean-based: use AND conditions on `?id=` to extract alice's secret from `users`, then `?secret=CTF{blind_sqli_hunter}` |
| 14 | SSRF Lab | `CTF{ssrf_internal_reached}` | `/c14?url=http://127.0.0.1:5000/internal/flag` |
| 15 | JWT Trap | `CTF{jwt_none_algorithm}` | Forge JWT with header `{"alg":"none"}`, payload `{"user":"admin","role":"admin"}`, empty signature |

## Running
```
pip install flask
python app.py
```
Then open http://127.0.0.1:5000
