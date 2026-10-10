"""Deployment generator — Dockerfiles, compose, CI/CD configuration."""
from __future__ import annotations

from typing import Any


def render_backend_dockerfile() -> str:
    return '''# Backend image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
'''


def render_frontend_dockerfile() -> str:
    return '''# Frontend image: build the SPA and serve it with nginx
FROM node:20-alpine AS build
WORKDIR /srv/web
COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /srv/web/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
'''


def render_nginx_conf() -> str:
    return '''server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
'''


def render_compose(spec: dict[str, Any]) -> str:
    name = spec["name"].lower().replace(" ", "-")
    return f'''services:
  backend:
    build: ./backend
    environment:
      APP_NAME: "{spec["name"]}"
      SECRET_KEY: ${{SECRET_KEY:-dev-only-secret-change-me}}
      DATABASE_URL: sqlite:////data/app.db
      CORS_ORIGINS: http://localhost:5173,http://localhost
    volumes:
      - {name}-data:/data
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request;urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 5s
      retries: 3

  frontend:
    build: ./frontend
    depends_on:
      - backend
    ports:
      - "5173:80"

volumes:
  {name}-data:
'''


def render_ci_workflow(spec: dict[str, Any]) -> str:
    return f'''name: CI — {spec["name"]}

on:
  push:
    branches: [main]
  pull_request:

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest
      - name: Run test suite
        run: cd backend && python -m pytest tests -q

  frontend-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - name: Build frontend
        run: cd frontend && npm install && npm run build
'''


def render_dockerignore() -> str:
    return ("__pycache__/\n*.pyc\n.venv/\napp.db\nnode_modules/\ndist/\n.git/\n.env\n")


def deployment_file_map(spec: dict[str, Any]) -> dict[str, str]:
    return {
        "backend/Dockerfile": render_backend_dockerfile(),
        "frontend/Dockerfile": render_frontend_dockerfile(),
        "frontend/nginx.conf": render_nginx_conf(),
        "docker-compose.yml": render_compose(spec),
        ".github/workflows/ci.yml": render_ci_workflow(spec),
        ".dockerignore": render_dockerignore(),
        ".gitignore": "__pycache__/\n*.pyc\n.venv/\napp.db\nnode_modules/\ndist/\n.env\n",
    }
