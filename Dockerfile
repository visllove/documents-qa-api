# Базовый образ
FROM python:3.11-slim

# Базовые переменные окружения
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Утилиты, нужные для скачивания моделей (git, git-lfs)
RUN apt-get update && \
    apt-get install -y --no-install-recommends git git-lfs && \
    git lfs install && \
    rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# ---------- зависимости ----------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- модели / эмбеддинги (optional, чтобы не качать на cold-start) ----------
RUN python - <<'PY'
from huggingface_hub import snapshot_download

CACHE = "/root/.cache/huggingface"

# 1) multilingual-e5-base (эмбеддинги)
snapshot_download(
    repo_id="intfloat/multilingual-e5-base",
    cache_dir=CACHE,
    allow_patterns=["model.safetensors", "config.json", "sentencepiece.*"],
)

# 2) Локальный LLM (для оффлайн-доступа)
#  В текущей версии не нужен, но при желании можно загрузить
# snapshot_download(
#     repo_id="Qwen/Qwen3-7B-Chat",
#     cache_dir=CACHE,
#     allow_patterns=["*.safetensors", "config.json", "tokenizer.*"],
# )
PY

ENV HF_HOME=/root/.cache/huggingface \
    TRANSFORMERS_CACHE=/root/.cache/huggingface

# ---------- приложение ----------
COPY app app

# Spaces проксирует порт, указанный в README (по умолчанию 7860)
EXPOSE 7860

# Hugging Face передаст переменную $PORT; если её нет — fallback на 7860
CMD ["bash", "-c", "uvicorn app.main:api --host 0.0.0.0 --port ${PORT:-7860}"]
