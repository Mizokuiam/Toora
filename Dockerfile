# Toora - use Docker build when Nixpacks fails to generate a plan
# Railway overrides CMD per service (web: uvicorn, worker: python -m worker.run)
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Default: web service (Railway overrides CMD for worker via Custom Start Command)
EXPOSE 8080
ENV PORT=8080
CMD uvicorn bot.webhook:app --host 0.0.0.0 --port ${PORT}
