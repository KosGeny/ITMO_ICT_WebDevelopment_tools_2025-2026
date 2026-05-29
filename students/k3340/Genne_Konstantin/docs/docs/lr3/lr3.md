# Лабораторная работа 3: Упаковка FastAPI приложения в Docker, Работа с источниками данных и Очереди

## Структура проекта

```
.
├── app/                          # Основное FastAPI-приложение
│   ├── main.py                   # Точка входа, подключение роутеров
│   ├── celery_app.py             # Конфигурация Celery (брокер Redis)
│   ├── celery_tasks.py           # Celery-задача для парсинга
│   ├── dockerfile                # Dockerfile для api и worker
│   ├── requirements.txt          # Зависимости основного приложения
│   ├── alembic.ini               # Конфигурация Alembic
│   ├── alembic/                  # Миграции БД
│   ├── core/
│   │   ├── auth.py               # JWT-аутентификация
│   │   ├── config.py             # Настройки (pydantic-settings)
│   │   └── database.py           # Подключение к БД (get_session)
│   ├── models/                   # SQLModel-модели
│   │   ├── user.py               # User, UserRole
│   │   ├── task.py               # Task, TaskStatus, TaskPriority
│   │   ├── tag.py                # Tag
│   │   ├── task_tag.py           # TaskTag (M2M)
│   │   ├── workspace.py          # Workspace
│   │   └── time_log.py           # TimeLog
│   ├── schemas/                  # Pydantic-схемы (request/response)
│   │   ├── user.py
│   │   ├── task.py
│   │   ├── tag.py
│   │   ├── task_tag.py
│   │   ├── workspace.py
│   │   ├── time_log.py
│   │   └── analytics.py
│   └── routers/                  # Эндпоинты
│       ├── auth.py               # Регистрация, логин, профиль
│       ├── tasks.py              # CRUD задач
│       ├── tags.py               # CRUD тегов
│       ├── workspaces.py         # CRUD рабочих пространств
│       ├── analytics.py          # Аналитика по времени
│       └── parser.py             # Парсинг GitHub Issues
│
├── parser_service/               # Микросервис парсера
│   ├── main.py                   # FastAPI-приложение парсера
│   ├── parser.py                 # Логика парсинга GitHub Issues
│   ├── dockerfile                # Dockerfile для parser
│   └── requirements.txt          # Зависимости парсера
│
├── docker-compose.yml            # Оркестрация всех сервисов
├── .env                          # Пример переменных окружения
```

---

## Эндпоинты

### Парсинг GitHub Issues (`/api/parser`)

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/parser/parse` | Прямой (синхронный) парсинг |
| POST | `/api/parser/parse/queue` | Асинхронный парсинг через Celery |
| GET | `/api/parser/status/{task_id}` | Статус асинхронной задачи |
| GET | `/api/parser/health` | Health check парсер-сервиса |

**POST `/api/parser/parse`** — синхронный вызов
```json
// Request
{ "url": "https://github.com/owner/repo/issues" }

// Response 200
{
  "success": true,
  "message": "Parsing completed successfully",
  "result": {
    "success": true,
    "tasks_created": 5,
    "tags_created": 3,
    "workspace": "owner/repo",
    "total_issues_found": 5
  }
}
```

**POST `/api/parser/parse/queue`** — асинхронный вызов через очередь задач
```json
// Request
{ "url": "https://github.com/owner/repo/issues" }

// Response 200
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PENDING",
  "message": "Parsing task has been queued"
}
```

**GET `/api/parser/status/{task_id}`** — проверка статуса
```json
// Response 200 (в процессе)
{
  "task_id": "550e8400-...",
  "status": "PROGRESS",
  "ready": false
}

// Response 200 (завершено)
{
  "task_id": "550e8400-...",
  "status": "SUCCESS",
  "ready": true,
  "result": {
    "success": true,
    "tasks_created": 5,
    "tags_created": 3,
    "workspace": "owner/repo",
    "total_issues_found": 5
  }
}
```

---

## Dockerfile

### `app/dockerfile` — для API и Worker

```dockerfile
FROM python:3.10-slim

WORKDIR /

RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY . /app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- **Базовый образ**: `python:3.10-slim` — минимальный образ Python 3.10
- **Утилиты**: `curl` — для healthcheck-ов
- **Зависимости**: устанавливаются из `requirements.txt` с кэшированием слоя
- **Команда**: по умолчанию запускает uvicorn; для worker переопределяется в `docker-compose.yml`

### `parser_service/dockerfile` — для микросервиса парсера

```dockerfile
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY parser_service/requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --upgrade -r requirements.txt

COPY parser_service/ .
COPY app/models/ ./app/models/
COPY app/__init__.py ./app/__init__.py

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

- **Рабочая директория**: `/app`
- **Копирование моделей**: парсер использует SQLModel-модели из `app/models/`
- **Порт**: 8001 (отдельный от основного API)

---

## Docker Compose

Файл `docker-compose.yml` описывает 5 сервисов:

| Сервис | Контейнер | Зависимости | Назначение |
|--------|-----------|-------------|------------|
| `postgres` | `db` | — | База данных PostgreSQL 16 Alpine |
| `redis` | `redis` | — | Брокер сообщений Redis 7 Alpine |
| `api` | `api` | postgres (healthy), redis (healthy) | Основное FastAPI-приложение |
| `parser` | `parser` | postgres (healthy) | Микросервис парсинга |
| `worker` | `worker` |  postgres (healthy), redis (started), parser (started) | Celery worker для фоновых задач |

**Ключевые особенности**:
- **Все сервисы** имеют `healthcheck` для контроля состояния
- **api** при запуске выполняет `alembic upgrade head` (миграции БД), затем запускает uvicorn
- **worker** использует тот же образ, что и api, но с другой командой запуска: `celery -A app.celery_app:celery_app worker --loglevel=INFO`
- **parser** собирается из корня проекта (`context: .`) с указанием `dockerfile: parser_service/dockerfile`
- **Переменные окружения** берутся из `.env` файла (все сервисы используют `env_file`)
- **Данные PostgreSQL** сохраняются в volume `postgres_data`
- **redis** и **parser** для worker используют `condition: service_started` (не ждут healthcheck)
- **restart policy**: `unless-stopped` для всех сервисов

---

## Зависимости

### `app/requirements.txt`
```
fastapi, uvicorn[standard], sqlmodel, psycopg2-binary,
python-dotenv, requests, celery, redis, alembic,
pydantic-settings, python-jose[cryptography],
passlib[bcrypt], bcrypt==4.0.1, email-validator,
python-multipart
```

### `parser_service/requirements.txt`
```
fastapi, uvicorn[standard], sqlmodel, psycopg2-binary,
python-dotenv, beautifulsoup4, requests, sqlalchemy
```

---

## Вывод к работе

В ходе выполнения лабораторной работы был внедрён парсинг задач как отдельный сервис к основному api менеджера времени и задач, FastAPI приложения были упакованы в docker, настроены эндпоинты для прямого вызова парсера из основного API и через Celery. Приложение готово к развёртыванию.