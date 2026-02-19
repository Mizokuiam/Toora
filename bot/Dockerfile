# bot/Dockerfile — built with rootDirectory=bot in Railway.
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY bot/requirements.txt ./bot/requirements.txt
RUN pip install --no-cache-dir -r bot/requirements.txt

COPY . .

ENV PYTHONPATH=/app
EXPOSE 8001

CMD ["uvicorn", "bot.main:app", "--host", "0.0.0.0", "--port", "8001"]
