# backend/Dockerfile — built with rootDirectory=backend in Railway.
# COPY paths are relative to the repo root (Railway build context = repo root).
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies — path is relative to repo root
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy full repo so core/ and db/ package imports work
COPY . .

ENV PYTHONPATH=/app
EXPOSE 8080

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
