FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/requirements.txt
COPY worker/requirements.txt ./worker/requirements.txt
COPY bot/requirements.txt ./bot/requirements.txt

RUN pip install --no-cache-dir \
    -r backend/requirements.txt \
    -r worker/requirements.txt \
    -r bot/requirements.txt

COPY . .

ENV PYTHONPATH=/app

# Start command is overridden per service in railway.toml
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
