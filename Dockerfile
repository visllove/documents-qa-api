FROM python:3.11-slim
    

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/app/.cache

# HF Space offline settings
    HF_HUB_OFFLINE=1 \
    HF_DATASETS_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1
    


RUN apt-get update && \
    apt-get install -y --no-install-recommends git git-lfs curl ca-certificates && \
    git lfs install && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Загрузка модели для эмбеддингов
RUN python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="intfloat/multilingual-e5-base",
    cache_dir="/app/.cache",
    allow_patterns=[
        "*.json","*.safetensors","*.bin",
        "sentencepiece*","vocab*","tokenizer*",
        "modules.json","*Pooling/**","*SentenceTransformer/**"
    ],
    local_dir_use_symlinks=False,
)
PY

# Новый юзер, чтобы запускать не от root
RUN useradd -m app && chown -R app /app
USER app


COPY app app


EXPOSE 7860
CMD ["bash", "-c", "uvicorn app.main:api --host 0.0.0.0 --port ${PORT:-7860}"]
