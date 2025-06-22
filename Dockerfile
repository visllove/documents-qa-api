FROM python:3.11-slim


ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/app/.cache \
    TRANSFORMERS_CACHE=/app/.cache


RUN apt-get update && \
    apt-get install -y --no-install-recommends git curl ca-certificates && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


RUN python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download(
    "intfloat/multilingual-e5-base",
    cache_dir="/app/.cache",
    allow_patterns=[
        "model.safetensors",
        "config.json",
        "sentencepiece.*",
        "tokenizer.json",
        "tokenizer_config.json",
    ],
)
PY

# Новый юзер, чтобы запускать не от root
RUN useradd -m app && chown -R app /app
USER app


COPY app app


EXPOSE 7860
CMD ["bash", "-c", "uvicorn app.main:api --host 0.0.0.0 --port ${PORT:-7860}"]
