# Root Dockerfile — builds the worker service by default.
# Railway uses this when the worker service has no explicit rootDirectory.
# The backend and bot services each have their own Dockerfile in their subdirectory.
FROM python:3.12-slim

WORKDIR /app

# System deps (needed by some Python packages)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install worker dependencies
COPY worker/requirements.txt ./worker/requirements.txt
RUN pip install --no-cache-dir -r worker/requirements.txt

# Copy full repo so relative imports (core/, db/, agent/) work
COPY . .

ENV PYTHONPATH=/app

# Default CMD = worker. Railway overrides this via Start Command in dashboard.
CMD ["python", "worker/main.py"]
