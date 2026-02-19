FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for some packages
RUN apt-get update && apt-get install -y --no-install-recommends gcc libffi-dev && rm -rf /var/lib/apt/lists/*

COPY worker/requirements.txt ./worker/requirements.txt
RUN pip install --no-cache-dir -r worker/requirements.txt

COPY . .

ENV PYTHONPATH=/app

CMD ["python", "worker/main.py"]
