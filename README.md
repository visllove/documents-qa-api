# Documents QA API

<p align="center">
  <img src="https://img.shields.io/badge/Стек-FastAPI • LangChain • Docker-blue" />
  <img src="https://img.shields.io/badge/LLM-Qwen3 / OpenRouter-orange" />
  <img src="https://img.shields.io/badge/Эмбеддинги-e5 multilingual-green" />
  <img src="https://img.shields.io/badge/License-MIT-green" />
</p>

REST API-сервис, который принимает **.DOCX-документы** и отвечает на вопросы к их содержимому:

* сохраняет и буферизует `.docx`;
* извлекает текст → режет его на чанки → строит эмбеддинги `intfloat/multilingual-e5-base`;
* кладёт векторы в **Chroma**;
* передаёт вопрос через **LangChain** в LLM (Qwen3 на OpenRouter или локальный в зависимости от выбора пользователя);
* возвращает JSON c готовым ответом или статусом прогресса.

Dockerfile поддерживает возможность деплоя на **Hugging Face Spaces**.

---

## Быстрый старт

```bash
git clone https://github.com/<your-org>/documents_qa_project.git
cd documents_qa_project
```

**Ключ OpenRouter (рекомендуется для быстрой работы LLM)**
```bash
echo "OPENROUTER_API_KEY=hf_xxx" > .env
echo "LLM_PROVIDER=openrouter" > .env
```

**Запуск с docker-compose**
```bash
docker compose up --build -d          # http://localhost:7860
curl -f http://localhost:7860/healthz # OK
open http://localhost:7860/docs       # Swagger UI
```

# Стек и возможности
* Приём .docx-файлов, API - FastAPI, python-docx
* Связь между компонентами, разбиение текста на чанки, retrieval - LangChain
* Векторное хранилище - Chroma
* Модель для эмбеддингов (локальная) - intfloat/multilingual-e5-base
* LLM -	Qwen3-32B-Free-Chat через Openrouter (требуется API-ключ) | любой локальный	через LangChain
* Контейнеризация	Python 3.11-slim + .venv	образ

**Переменные окружения**
* OPENROUTER_API_KEY	—	ключ доступа к OpenRouter
* LLM_PROVIDER	openrouter	openrouter / local
* PORT	7860	порт для uvicorn внутри контейнера
* HF_HOME	/app/.cache/huggingface	- кеш

**REST API**
- POST	/files 201 {file_id} -	Загрузить .docx
- POST	/files/{file_id}/questions	202 {question_id} -	Задать вопрос по указанному документу
- GET	/questions/{question_id}	200 {status, answer}	- Получить ответ / статус

**Пример работы с API (bash + jq)**
```bash
id=$(curl -sF file=@Договор.docx localhost:7860/files | jq -r .file_id)
qid=$(curl -s -X POST -H "Content-Type: application/json" \
      -d '{"question":"Укажи предмет договора"}' \
      localhost:7860/files/$id/questions     | jq -r .question_id)
curl localhost:7860/questions/$qid
```


**Деплой в Hugging Face Spaces**
```bash
huggingface-cli repo create documents_qa_project --type=space --sdk docker
git remote add origin https://huggingface.co/spaces/<user>/documents_qa_project.git
git push -u origin main
```

# Работающая версия на HuggingFace:
https://vislove-documents-qa-api.hf.space/docs
