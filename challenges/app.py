"""HackQuest CTF - entrypoint shim.
The live arena lives in rounds.py (5-round progressive CTF).
This module re-exports it so BOTH `gunicorn app:app` and `gunicorn rounds:app`
work, regardless of how the host service is configured.
"""
from rounds import app  # noqa: F401

if __name__ == "__main__":
    from rounds import PORT
    app.run(host="0.0.0.0", debug=True, port=int(PORT))