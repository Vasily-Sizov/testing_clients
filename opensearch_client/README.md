# OpenSearch Client

Переиспользуемый клиент для работы с OpenSearch, включающий FastAPI роуты и lifecycle управление.

## Структура проекта

```
opensearch/
├── client/              # Клиент для работы с OpenSearch
│   ├── client.py       # Основные методы работы с OpenSearch
│   └── connection.py    # Создание соединения
├── entities.py          # Модели данных для API запросов
├── routes.py            # FastAPI роуты
├── lifespan.py          # Управление жизненным циклом приложения
├── pyproject.toml       # Конфигурация проекта и зависимости
├── uv.lock              # Файл блокировки версий зависимостей (uv)
├── test_app/           # Тестовое приложение
│   ├── main.py         # FastAPI приложение
│   └── requirements.txt
└── tests/              # Тесты
    ├── test_routes.py   # Интеграционные тесты (API роуты + клиент)
    └── conftest.py      # Общие фикстуры для тестов
```

## Требования

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) - быстрый менеджер пакетов Python
- Docker и Docker Compose (для запуска тестового приложения)
- OpenSearch 2.x+ (для интеграционных тестов)

### Установка uv

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Запуск проекта

### Использование Docker Compose

Проект включает docker-compose конфигурацию для запуска тестового приложения с OpenSearch:

```bash
docker-compose up --build
```

После запуска:
- OpenSearch доступен на `http://localhost:9200`
- API приложение доступно на `http://localhost:8000`
- Документация API: `http://localhost:8000/docs`

### Локальный запуск

1. Установите зависимости:

```bash
# Установить все зависимости (включая тестовые)
uv sync --extra test

# Или только основные зависимости
uv sync
```

2. Настройте переменные окружения:

```bash
# Windows (cmd)
set OPENSEARCH_HOSTS=http://localhost:9200
set OPENSEARCH_USERNAME=  # опционально
set OPENSEARCH_PASSWORD=  # опционально

# Linux/macOS
export OPENSEARCH_HOSTS=http://localhost:9200
export OPENSEARCH_USERNAME=  # опционально
export OPENSEARCH_PASSWORD=  # опционально
```

3. Запустите приложение:

```bash
# Используя uv
uv run uvicorn test_app.main:app --host 0.0.0.0 --port 8000

# Или активируйте виртуальное окружение и запустите напрямую
# uv venv  # если нужно создать venv явно
# source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows
# uvicorn test_app.main:app --host 0.0.0.0 --port 8000
```

## Запуск тестов

Перед запуском тестов убедитесь, что установлены все зависимости:

```bash
uv sync --extra test
```

### Интеграционные тесты

Все тесты являются интеграционными и требуют запущенный OpenSearch сервер.
Тесты проверяют как работу API роутов через HTTP, так и работу клиента OpenSearchClient напрямую.

```bash
# Запустите OpenSearch (например, через docker-compose)
docker-compose up opensearch -d

# Настройте переменные окружения
# Windows (cmd)
set OPENSEARCH_HOSTS=http://localhost:9200

# Linux/macOS
export OPENSEARCH_HOSTS=http://localhost:9200

# Запустите все интеграционные тесты
uv run pytest tests/ -m integration -v

# Или запустите конкретный файл
uv run pytest tests/test_routes.py -m integration -v
```

## Использование в проекте

### Импорт модуля

```python
from opensearch.client import OpenSearchClient, create_opensearch_connection
from opensearch.routes import router
from opensearch.lifespan import opensearch_lifespan
```

### Настройка FastAPI приложения

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from opensearch.lifespan import opensearch_lifespan
from opensearch.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with opensearch_lifespan(
        app=app,
        hosts=["http://localhost:9200"],
        username=None,
        password=None,
    ):
        yield

app = FastAPI(lifespan=lifespan)
app.include_router(router)
```

## API эндпоинты

- `GET /opensearch/ping` - проверка доступности OpenSearch
- `GET /opensearch/info` - информация о кластере
- `GET /opensearch/indices` - список индексов
- `POST /opensearch/indices/{name}/exists` - проверка существования индекса
- `POST /opensearch/indices/{name}/create` - создание индекса
- `POST /opensearch/documents/index` - индексация документа
- `POST /opensearch/documents/bulk-index` - массовая индексация
- `POST /opensearch/documents/get` - получение документа по ID
- `POST /opensearch/documents/bulk-get` - получение нескольких документов
- `POST /opensearch/search/vector` - векторный поиск (kNN)
- `POST /opensearch/search/bm25` - BM25 текстовый поиск
- `POST /opensearch/search/hybrid` - гибридный поиск (векторный + BM25)

Полная документация доступна по адресу `/docs` при запущенном приложении.

## Управление зависимостями

Проект использует [uv](https://github.com/astral-sh/uv) для управления зависимостями.

### Основные команды

```bash
# Установить все зависимости
uv sync

# Установить зависимости с тестовыми пакетами
uv sync --extra test

# Добавить новую зависимость
uv add package-name

# Добавить dev-зависимость (в optional-dependencies)
uv add --optional test package-name

# Удалить зависимость
uv remove package-name

# Обновить все зависимости
uv sync --upgrade

# Запустить команду в uv окружении
uv run python script.py
uv run pytest
uv run uvicorn test_app.main:app
```

### Структура зависимостей

- Основные зависимости указаны в `[project.dependencies]` в `pyproject.toml`
- Тестовые зависимости указаны в `[project.optional-dependencies.test]`
- Версии всех зависимостей зафиксированы в `uv.lock`

## Лицензия

Проект предназначен для внутреннего использования.

