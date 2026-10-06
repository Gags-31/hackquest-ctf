# HackQuest CTF — Challenge Lab
All-in-one vulnerable web app for local practice. Run: `python app.py`, open http://localhost:5000

Flags and solutions are in FLAGS.md.

## Deploy online (Render)
1. Push this repo to GitHub.
2. Create a Render Web Service from the repo (`render.yaml` at repo root auto-configures it), or set manually:
   - Build: `pip install -r challenges/requirements.txt`
   - Start: `gunicorn app:app` (from the `challenges/` directory)
3. Your challenges will be at `https://<app>.onrender.com/`.

Note: gunicorn does not run on Windows — use it on Linux hosts (Render/Railway).
For PythonAnywhere, use `app.py` as a Flask WSGI app directly.
