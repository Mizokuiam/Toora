# Root Dockerfile — single image for all Python services.
# The SERVICE build arg selects which service to run.
# Railway overrides CMD via "Start Command" per service:
#   backend/web: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
#   bot:         uvicorn bot.main:app --host 0.0.0.0 --port $PORT
#   worker:      python worker/main.py

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install all Python dependencies for all services
COPY backend/requirements.txt ./backend/requirements.txt
COPY worker/requirements.txt ./worker/requirements.txt
COPY bot/requirements.txt ./bot/requirements.txt

RUN pip install --no-cache-dir \
    -r backend/requirements.txt \
    -r worker/requirements.txt \
    -r bot/requirements.txt

# Copy full repo so all packages are importable
COPY . .

ENV PYTHONPATH=/app
EXPOSE 8080

# Default CMD is backend; Railway overrides this per service via Start Command
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
