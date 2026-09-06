# syntax=docker/dockerfile:1

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=120

WORKDIR /app

# curl = healthcheck; build tools help if a package lacks a prebuilt wheel
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    git \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install CPU torch first (smaller/more reliable than default CUDA-oriented resolve),
# then the rest of the app deps.
RUN pip install --upgrade pip \
  && pip install --index-url https://download.pytorch.org/whl/cpu torch \
  && pip install -r requirements.txt

COPY app ./app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
