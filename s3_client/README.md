# S3 Client

Переиспользуемый клиент для работы с S3 объектным хранилищем, включающий FastAPI роуты и lifecycle управление.

## Структура проекта

```
s3_client/
├── my_s3_client/        # Основной модуль
│   ├── client/         # Клиент для работы с S3
│   │   ├── client.py  # Основные методы работы с объектами
│   │   ├── connection.py  # Создание соединения
│   │   └── utils.py   # Утилиты
│   └── endpoint/      # FastAPI эндпоинты
│       ├── routes.py  # FastAPI роуты
│       ├── lifespan.py  # Управление жизненным циклом приложения
│       ├── entities.py  # Модели данных для API запросов
│       └── base_settings.py  # Настройки приложения
├── test_app/          # Тестовое приложение
│   └── main.py        # Точка входа тестового приложения
├── tests/             # Тесты
│   ├── test_routes.py # Интеграционные тесты
│   └── conftest.py    # Общие фикстуры для тестов
└── pyproject.toml     # Конфигурация проекта и зависимости
```

## Требования

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) - быстрый менеджер пакетов Python
- Docker и Docker Compose (для запуска тестового приложения)
- S3-совместимое хранилище (AWS S3, MinIO и т.д.)

### Установка uv

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Запуск проекта

### Использование Docker Compose

Проект включает docker-compose конфигурацию для запуска тестового приложения с MinIO:

```bash
docker-compose up --build
```

После запуска:
- MinIO доступен на `localhost:9000`
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
set AWS_ACCESS_KEY_ID=your_access_key
set AWS_SECRET_ACCESS_KEY=your_secret_key
set AWS_REGION=us-east-1
set AWS_ENDPOINT_URL=http://localhost:9000  # для MinIO
set AWS_USE_SSL=false
set AWS_VERIFY=false

# Linux/macOS
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
export AWS_ENDPOINT_URL=http://localhost:9000  # для MinIO
export AWS_USE_SSL=false
export AWS_VERIFY=false
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

Все тесты являются интеграционными и требуют запущенный S3-совместимый сервер (например, MinIO).

```bash
# Запустите MinIO (например, через docker-compose)
docker-compose up minio -d
```

#### Запуск тестов (рекомендуемый способ)

Тесты имеют значения по умолчанию для локального MinIO, поэтому можно запускать их без установки переменных окружения:

```bash
# Просто запустите тесты - значения по умолчанию:
# - AWS_ACCESS_KEY_ID=minioadmin
# - AWS_SECRET_ACCESS_KEY=minioadmin
# - AWS_REGION=us-east-1
# - AWS_ENDPOINT_URL=http://localhost:9000
# - AWS_USE_SSL=false
# - AWS_VERIFY=false

# Работает в Windows CMD, bash (Linux/macOS/Git Bash) и других оболочках:
uv run pytest tests/ -m integration -v

# Или с дополнительными опциями:
uv run pytest tests/ -m integration -v --tb=line -x
```

**Примечание:** В bash команда `uv run pytest tests/ -m integration -v` работает напрямую без установки переменных окружения, так как тесты используют значения по умолчанию для MinIO.

#### Запуск тестов с переопределением переменных окружения

Если нужно использовать другие настройки, можно установить переменные окружения:

**Windows (cmd):**
```bash
set AWS_ACCESS_KEY_ID=minioadmin
set AWS_SECRET_ACCESS_KEY=minioadmin
set AWS_REGION=us-east-1
set AWS_ENDPOINT_URL=http://localhost:9000
set AWS_USE_SSL=false
set AWS_VERIFY=false
uv run pytest tests/ -m integration -v
```

**Linux/macOS или Git Bash:**

Вариант 1: Использовать скрипт (рекомендуется для bash):
```bash
bash run_tests.sh
```

Вариант 2: Установить переменные и запустить в одной команде:
```bash
AWS_ACCESS_KEY_ID=minioadmin AWS_SECRET_ACCESS_KEY=minioadmin AWS_REGION=us-east-1 AWS_ENDPOINT_URL=http://localhost:9000 AWS_USE_SSL=false AWS_VERIFY=false uv run pytest tests/ -m integration -v
```

**Важно для bash:** При использовании `export` и `&&` в одной строке переменные окружения могут не передаваться в процесс, запущенный через `uv run`. Используйте скрипт `run_tests.sh` или устанавливайте переменные в одной команде (как в варианте 2).

## Использование в проекте

### Импорт модуля

```python
from my_s3_client.client import S3Client, create_s3_client
from my_s3_client.endpoint.routes import s3_router
from my_s3_client.endpoint.lifespan import s3_lifespan
```

### Настройка FastAPI приложения

```python
from fastapi import FastAPI
from my_s3_client.endpoint.lifespan import s3_lifespan
from my_s3_client.endpoint.routes import s3_router

app = FastAPI(lifespan=s3_lifespan)
app.include_router(s3_router)
```

Настройки подключения к S3 загружаются автоматически из переменных окружения (см. раздел "Настройка переменных окружения").

## API эндпоинты

### Общие

- `GET /s3/ping` - проверка доступности S3
- `GET /s3/buckets` - список всех bucket'ов
- `POST /s3/buckets/exists` - проверка существования bucket'а
- `POST /s3/buckets/create` - создание bucket'а
- `POST /s3/buckets/delete` - удаление bucket'а

### Объекты

- `POST /s3/objects/upload` - загрузка объекта в S3
- `POST /s3/objects/download` - скачивание объекта из S3
- `POST /s3/objects/delete` - удаление объекта
- `POST /s3/objects/exists` - проверка существования объекта
- `POST /s3/objects/list` - список объектов в bucket'е
- `POST /s3/objects/metadata` - получение метаданных объекта
- `POST /s3/objects/copy` - копирование объекта
- `POST /s3/objects/presigned-url` - генерация presigned URL

Полная документация доступна по адресу `/docs` при запущенном приложении.

## Методы клиента

### Операции с bucket'ами

- `list_buckets()` - список всех bucket'ов
- `bucket_exists()` - проверка существования bucket'а
- `create_bucket()` - создание bucket'а
- `delete_bucket()` - удаление bucket'а

### Операции с объектами

- `upload_object()` - загрузка объекта
- `download_object()` - скачивание объекта
- `delete_object()` - удаление объекта
- `object_exists()` - проверка существования
- `list_objects()` - список объектов
- `get_object_metadata()` - получение метаданных
- `copy_object()` - копирование объекта
- `generate_presigned_url()` - генерация presigned URL

### Примеры использования

```python
from my_s3_client.client import S3Client, create_s3_client

# Создание сессии
session = create_s3_client(
    aws_access_key_id="your_key",
    aws_secret_access_key="your_secret",
    endpoint_url="http://localhost:9000",  # для MinIO
)
client = S3Client(
    session=session,
    endpoint_url="http://localhost:9000",
    use_ssl=False,
    verify=False,
)

# Загрузка объекта
await client.upload_object(
    bucket_name="my-bucket",
    object_key="path/to/file.txt",
    data=b"file content",
    content_type="text/plain",
)

# Скачивание объекта
data = await client.download_object(
    bucket_name="my-bucket",
    object_key="path/to/file.txt",
)

# Список объектов
objects = await client.list_objects(
    bucket_name="my-bucket",
    prefix="path/",
)

# Удаление объекта
await client.delete_object(
    bucket_name="my-bucket",
    object_key="path/to/file.txt",
)
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
uv run pytest
uv run uvicorn test_app.main:app
```

### Структура зависимостей

- Основные зависимости указаны в `[project.dependencies]` в `pyproject.toml`
- Тестовые зависимости указаны в `[project.optional-dependencies.test]`
- Версии всех зависимостей зафиксированы в `uv.lock`

## Лицензия

Проект предназначен для внутреннего использования.

