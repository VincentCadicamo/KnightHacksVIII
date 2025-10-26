ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /KnightHacksVIII
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt requirements.txt
COPY src ./src
COPY data ./data

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "./src/solve_vrp.py"]