FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY pyproject.toml requirements.txt ./
COPY src ./src
COPY schemas ./schemas
COPY tests ./tests
COPY benchmarks ./benchmarks
COPY experiments ./experiments
COPY paper/hsp-agile ./paper/hsp-agile
COPY scripts ./scripts
COPY check_progress.py ./

RUN pip install --no-cache-dir -e . \
    && pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/workspace
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["bash", "scripts/reproduce.sh"]
