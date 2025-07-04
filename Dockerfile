FROM python:3.11-slim
    

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/app/.cache/huggingface \
    PATH="/opt/.venv/bin:$PATH"

RUN apt-get update && \
    apt-get install -y --no-install-recommends git git-lfs curl ca-certificates && \
    git lfs install && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app


# venv
RUN python -m venv /opt/.venv
RUN /opt/.venv/bin/pip install --upgrade pip

#  install pip requirements
COPY requirements.txt .
RUN /opt/.venv/bin/pip install --no-cache-dir -r requirements.txt

# Загрузка модели для эмбеддингов
RUN python - <<'PY'
from pathlib import Path
from os import getenv
from huggingface_hub import snapshot_download

hub_cache = Path(getenv("HF_HOME")) / "hub"
hub_cache.mkdir(parents=True, exist_ok=True)

snapshot_download(
    repo_id="intfloat/multilingual-e5-base",
    cache_dir=hub_cache,
    allow_patterns=[
        "*.json","*.safetensors","*.bin",
        "sentencepiece*","vocab*","tokenizer*",
        "modules.json","*Pooling/**","*SentenceTransformer/**"
    ],
    local_dir_use_symlinks=False,
)
PY


# HF Space offline settings
ENV HF_HUB_OFFLINE=1 \
    HF_DATASETS_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1


# Новый юзер, чтобы запускать не от root
RUN useradd -m app && chown -R app:app "$HF_HOME" /app
USER app

COPY app app


# Порт
EXPOSE 7860
CMD ["bash", "-c", "uvicorn app.main:api --host 0.0.0.0 --port ${PORT:-7860}"]
