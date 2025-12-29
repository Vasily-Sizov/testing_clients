# Redis Client

Переиспользуемый клиент для работы с Redis очередями, включающий FastAPI роуты и lifecycle управление.

## Структура проекта

```
redis_client/
├── my_redis_client/     # Основной пакет
│   ├── client/          # Клиент для работы с Redis
│   │   ├── client.py   # Основные методы работы с очередями
│   │   └── connection.py # Создание соединения
│   └── endpoint/        # FastAPI эндпоинты
│       ├── routes.py    # FastAPI роуты
│       ├── lifespan.py # Управление жизненным циклом приложения
│       ├── entities.py  # Модели данных для API запросов
│       └── base_settings.py # Настройки подключения
├── test_app/            # Тестовое приложение
│   └── main.py          # FastAPI приложение для тестирования
├── tests/               # Тесты
│   ├── test_routes.py   # Интеграционные тесты
│   └── conftest.py      # Общие фикстуры для тестов
├── pyproject.toml       # Конфигурация проекта и зависимости
└── README.md
```

## Требования

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) - быстрый менеджер пакетов Python
- Docker и Docker Compose (для запуска тестового приложения)
- Redis 6.0+ (для интеграционных тестов)

### Установка uv

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Запуск проекта

### Использование Docker Compose

Проект включает docker-compose конфигурацию для запуска тестового приложения с Redis:

```bash
docker-compose up --build
```

После запуска:
- Redis доступен на `localhost:6379`
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
set REDIS_HOST=localhost
set REDIS_PORT=6379
set REDIS_DB=0
set REDIS_PASSWORD=  # опционально

# Linux/macOS
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
export REDIS_PASSWORD=  # опционально
```

3. Запустите приложение:

```bash
# Используя uv
uv run uvicorn test_app.main:app --host 0.0.0.0 --port 8000
```

## Запуск тестов

Перед запуском тестов убедитесь, что установлены все зависимости:

```bash
uv sync --extra test
```

### Интеграционные тесты

Все тесты являются интеграционными и требуют запущенный Redis сервер.

**Важно:** Тесты запускаются **локально** на вашей машине, но подключаются к Redis, который должен быть запущен (например, в контейнере). Тесты создают своё собственное FastAPI приложение через фикстуры и **не используют** контейнер `test-app` (который нужен только для демонстрации).

```bash
# Запустите только Redis (например, через docker-compose)
docker-compose up redis -d

# Настройте переменные окружения для тестов
# Windows (cmd)
set REDIS_HOST=localhost
set REDIS_PORT=6379

# Linux/macOS
export REDIS_HOST=localhost
export REDIS_PORT=6379

# Запустите все интеграционные тесты локально
uv run python -m pytest tests/ -m integration -v
```

**Как это работает:**
- Redis запущен в контейнере и доступен на `localhost:6379` (порт проброшен)
- Тесты запускаются локально через `pytest`
- Тесты создают своё FastAPI приложение через фикстуру `integration_app` в `conftest.py`
- Тесты подключаются к Redis на `localhost:6379` (который работает в контейнере)
- Контейнер `test-app` используется только для демонстрации работы API, тесты его не используют

## Использование в проекте

### Импорт модуля

```python
from my_redis_client.client.client import RedisClient
from my_redis_client.client.connection import create_redis_connection
from my_redis_client.endpoint.routes import redis_router
from my_redis_client.endpoint.lifespan import redis_lifespan
from my_redis_client.endpoint.base_settings import RedisSettings, get_settings
```

### Настройка FastAPI приложения

```python
from fastapi import FastAPI
from my_redis_client.endpoint.routes import redis_router

app = FastAPI()

# Подключаем роутер
# Lifespan для Redis автоматически настроен в роутере через redis_lifespan
app.include_router(redis_router)
```

**Важно:** Роутер `redis_router` уже содержит настроенный `lifespan`, который автоматически создаёт и управляет соединением с Redis при старте приложения. Настройки подключения берутся из переменных окружения (префикс `REDIS_`) или из файла `.env`.

## API эндпоинты

### Общие

- `GET /redis/ping` - проверка доступности Redis
- `GET /redis/info` - информация о Redis сервере
- `GET /redis/queues` - список всех очередей (с паттерном)

### Очереди

- `POST /redis/queues/push` - добавление сообщения в очередь
- `POST /redis/queues/pop` - извлечение сообщения из очереди (неблокирующая)
- `POST /redis/queues/blocking-pop` - извлечение сообщения из очереди (блокирующая)
- `POST /redis/queues/peek` - просмотр элементов очереди без удаления
- `POST /redis/queues/size` - получение размера очереди
- `POST /redis/queues/clear` - очистка очереди
- `POST /redis/queues/exists` - проверка существования очереди

Полная документация доступна по адресу `/docs` при запущенном приложении.

## Методы клиента

### Основные операции

- `queue_push()` - добавить сообщение в очередь (LPUSH/RPUSH)
- `queue_pop()` - извлечь сообщение из очереди (LPOP/RPOP)
- `queue_blocking_pop()` - блокирующее извлечение (BLPOP/BRPOP)
- `queue_peek()` - просмотр элементов без удаления
- `queue_size()` - размер очереди
- `queue_clear()` - очистка очереди
- `queue_exists()` - проверка существования
- `queue_list_all()` - список всех очередей

### Примеры использования

```python
from my_redis_client.client.client import RedisClient
from my_redis_client.client.connection import create_redis_connection

# Создание соединения
connection = create_redis_connection(host="localhost", port=6379)
client = RedisClient(connection)

# Добавление сообщения
await client.queue_push("my_queue", {"task": "process_data", "id": 123})

# Извлечение сообщения
message = await client.queue_pop("my_queue")

# Блокирующее извлечение (ждёт до 10 секунд)
result = await client.queue_blocking_pop("my_queue", timeout=10)

# Размер очереди
size = await client.queue_size("my_queue")

# Просмотр элементов
messages = await client.queue_peek("my_queue", count=5)
```

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
uv run python -m pytest tests/ -m integration -v
uv run uvicorn test_app.main:app
```

### Структура зависимостей

- Основные зависимости указаны в `[project.dependencies]` в `pyproject.toml`
- Тестовые зависимости указаны в `[project.optional-dependencies.test]`
- Версии всех зависимостей зафиксированы в `uv.lock`

## Лицензия

Проект предназначен для внутреннего использования.

