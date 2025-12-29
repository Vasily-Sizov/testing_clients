# Artemis Client

Переиспользуемый клиент для работы с Artemis очередями, включающий FastAPI роуты и lifecycle управление.

## Структура проекта

```
artemis_client/
├── my_artemis_client/     # Основной пакет
│   ├── client/          # Клиент для работы с Artemis
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
- Apache Artemis или ActiveMQ Artemis (для интеграционных тестов)

### Установка uv

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Запуск проекта

### Использование Docker Compose

Проект включает docker-compose конфигурацию для запуска тестового приложения с Artemis:

```bash
docker-compose up --build
```

После запуска:
- Artemis доступен на `localhost:61616` (AMQP) и `localhost:8161` (веб-консоль)
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
set ARTEMIS_URL=amqp://localhost:61616
set ARTEMIS_USERNAME=artemis
set ARTEMIS_PASSWORD=artemis

# Linux/macOS
export ARTEMIS_URL=amqp://localhost:61616
export ARTEMIS_USERNAME=artemis
export ARTEMIS_PASSWORD=artemis
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

Все тесты являются интеграционными и требуют запущенный Artemis сервер.

**Важно:** Тесты запускаются **локально** на вашей машине, но подключаются к Artemis, который должен быть запущен (например, в контейнере). Тесты создают своё собственное FastAPI приложение через фикстуры и **не используют** контейнер `test-app` (который нужен только для демонстрации).

```bash
# Запустите только Artemis (например, через docker-compose)
docker-compose up artemis -d

# Настройте переменные окружения для тестов
# Windows (cmd)
set ARTEMIS_URL=amqp://artemis:artemis@localhost:61616
set ARTEMIS_USERNAME=artemis
set ARTEMIS_PASSWORD=artemis

# Linux/macOS
export ARTEMIS_URL=amqp://artemis:artemis@localhost:61616
export ARTEMIS_USERNAME=artemis
export ARTEMIS_PASSWORD=artemis

# Запустите все интеграционные тесты локально
uv run python -m pytest tests/ -m integration -v
```

**Как это работает:**
- Artemis запущен в контейнере и доступен на `localhost:61616` (порт проброшен)
- Тесты запускаются локально через `pytest`
- Тесты создают своё FastAPI приложение через фикстуру `integration_app` в `conftest.py`
- Тесты подключаются к Artemis на `localhost:61616` (который работает в контейнере)
- Контейнер `test-app` используется только для демонстрации работы API, тесты его не используют

## Использование в проекте

### Импорт модуля

```python
from my_artemis_client.client.client import ArtemisClient
from my_artemis_client.endpoint.routes import artemis_router
from my_artemis_client.endpoint.lifespan import artemis_lifespan
from my_artemis_client.endpoint.base_settings import ArtemisSettings, get_settings
```

### Настройка FastAPI приложения

```python
from fastapi import FastAPI
from my_artemis_client.endpoint.routes import artemis_router

app = FastAPI()

# Подключаем роутер
# Lifespan для Artemis автоматически настроен в роутере через artemis_lifespan
app.include_router(artemis_router)
```

**Важно:** Роутер `artemis_router` уже содержит настроенный `lifespan`, который автоматически создаёт и управляет клиентом Artemis при старте приложения. Настройки подключения берутся из переменных окружения (префикс `ARTEMIS_`) или из файла `.env`.

## API эндпоинты

### Очереди

- `POST /artemis/send` - отправка сообщения в очередь Artemis

Полная документация доступна по адресу `/docs` при запущенном приложении.

## Методы клиента

### Основные операции

- `send_message(queue: str, body: str) -> bool` - отправка сообщения в очередь (асинхронная)
- `send_message_sync(queue: str, body: str) -> bool` - отправка сообщения в очередь (синхронная)

### Примеры использования

```python
from my_artemis_client.client.client import ArtemisClient
from my_artemis_client.endpoint.base_settings import get_settings

# Создание клиента
settings = get_settings()
connection_url = settings.get_connection_url()  # Формирует URL с учётными данными
client = ArtemisClient(connection_url)

# Или напрямую указать URL
client = ArtemisClient("amqp://artemis:artemis@localhost:61616")

# Отправка сообщения (асинхронная)
await client.send_message("chat.out", "Привет, мир!")

# Отправка сообщения (синхронная)
client.send_message_sync("email.out", "Test email message")
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

