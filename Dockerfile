FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt


FROM python:3.11-slim-bookworm

WORKDIR /app

COPY --from=builder /install /usr/local
COPY app ./app
COPY docs ./docs
COPY README.md ./

RUN mkdir -p /app/data/raw /app/data/processed /app/benchmarks \
    && chmod -R 777 /app/data /app/benchmarks

ENV PYTHONUNBUFFERED=1 \
    PORT=8000 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
