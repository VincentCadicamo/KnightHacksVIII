# syntax=docker/dockerfile:1.6
ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml* ./
COPY requirements.txt requirements.txt
COPY requirements-dev.txt requirements-dev.txt
RUN python -m pip install --upgrade pip && \
    (test -f requirements.txt && pip install -r requirements.txt || true) && \
    (test -f requirements-dev.txt && pip install -r requirements-dev.txt || true) && \
    pip install build pytest pytest-cov mypy
COPY src ./src
COPY tests ./tests
COPY data ./data
COPY scripts ./scripts

FROM base AS test
ENV OUT_DIR=/out
RUN mkdir -p "$OUT_DIR"
CMD bash -lc '\
  mypy src && \
  pytest -q --cov=src --cov-report=term-missing && \
  python -m build && \
  if [ -f scripts/build_dist_bin.py ]; then python scripts/build_dist_bin.py; fi && \
  mkdir -p "$OUT_DIR" && cp -r dist "$OUT_DIR"/ && if [ -d output ]; then cp -r output "$OUT_DIR"/; fi \
'
