# Build stage: compile the React/TypeScript SPA
FROM node:22-alpine AS build
WORKDIR /fe
COPY frontend/package*.json ./
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# Runtime stage: FastAPI serving the built SPA and the API
FROM python:3.12-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0

COPY backend/ ./
COPY --from=build /fe/dist ./frontend/dist

# Non-root user
RUN useradd --create-home --shell /usr/sbin/nologin appuser \
 && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/api/health || exit 1

CMD ["sh", "-c", "gunicorn app.main:app --bind 0.0.0.0:${PORT} --workers 2 --threads 4 --timeout 60 --access-logfile -"]