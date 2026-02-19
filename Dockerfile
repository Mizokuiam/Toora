# Root Dockerfile — used by both the 'web' (backend) and 'worker' services.
# Railway overrides CMD per service via "Start Command" in the dashboard.
# Default CMD here = backend (FastAPI), since 'web' is the public-facing service.
# Worker service overrides CMD to: python worker/main.py
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install all Python dependencies (backend + worker + bot share most of them)
COPY backend/requirements.txt ./backend/requirements.txt
COPY worker/requirements.txt ./worker/requirements.txt
COPY bot/requirements.txt ./bot/requirements.txt

RUN pip install --no-cache-dir \
    -r backend/requirements.txt \
    -r worker/requirements.txt \
    -r bot/requirements.txt

# Copy full repo so all packages (core/, db/, agent/, backend/, worker/, bot/) are importable
COPY . .

ENV PYTHONPATH=/app
EXPOSE 8080

# Default: backend (FastAPI). Worker service overrides this via Railway start command.
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
