#!/usr/bin/env python
"""QuantBuild one-command launcher.

Starts the backend API (and serves the built frontend if frontend/dist exists):

    python run.py [--port 8000]

For frontend development, run Vite separately:  cd frontend && npm run dev
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(BACKEND))


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch QuantBuild")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--reload", action="store_true", help="auto-reload on code changes")
    args = parser.parse_args()

    import uvicorn

    dist = Path(__file__).resolve().parent / "frontend" / "dist"
    print("⚡ QuantBuild")
    print(f"   API + UI : http://{args.host}:{args.port}")
    print(f"   API docs : http://{args.host}:{args.port}/docs")
    if not dist.exists():
        print("   (frontend/dist not built — run `cd frontend && npm install && npm run build`,")
        print("    or use `npm run dev` for the Vite dev server on :5173)")
    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload,
                reload_dirs=[str(BACKEND / "app")] if args.reload else None)


if __name__ == "__main__":
    main()
