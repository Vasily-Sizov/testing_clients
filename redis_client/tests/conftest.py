"""
Общие фикстуры для тестов Redis.
"""
import pytest
from redis.asyncio import Redis

from client.client import RedisClient
from client.connection import create_redis_connection
from base_settings import get_settings


@pytest.fixture(scope="module")
def event_loop():
    """
    Создаёт event loop для модуля тестов.
    """
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def redis_connection() -> Redis:
    """
    Создаёт соединение с Redis для тестов.

    Использует настройки из base_settings.py.
    """
    settings = get_settings()

    connection = create_redis_connection(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        password=settings.redis_password,
        decode_responses=False,  # Для тестов используем bytes
    )

    yield connection

    # Закрываем соединение после тестов
    await connection.aclose()


@pytest.fixture(scope="module")
async def client(redis_connection: Redis) -> RedisClient:
    """
    Создаёт RedisClient для тестов клиента напрямую.
    """
    return RedisClient(redis_connection)


@pytest.fixture(scope="module")
async def integration_client(redis_connection: Redis) -> RedisClient:
    """
    Создаёт RedisClient для интеграционных тестов API.
    """
    return RedisClient(redis_connection)


@pytest.fixture(scope="module")
def integration_app(redis_connection: Redis):
    """
    Создаёт FastAPI приложение для интеграционных тестов API.
    """
    from fastapi import FastAPI
    from routes import router
    from client.client import RedisClient

    app = FastAPI()
    app.include_router(router)

    # Инициализируем клиент напрямую
    client = RedisClient(redis_connection)
    app.state.redis_client = client
    app.state.redis_connection = redis_connection

    return app


@pytest.fixture(scope="module")
async def integration_test_client(integration_app):
    """
    Создаёт httpx.AsyncClient для интеграционных тестов API.
    """
    import httpx
    async with httpx.AsyncClient(app=integration_app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def test_queue(redis_connection: Redis) -> str:
    """
    Создаёт тестовую очередь и очищает её перед и после каждого теста.

    :return: имя тестовой очереди
    """
    queue_name = "test-queue"

    # Очищаем очередь перед каждым тестом
    await redis_connection.delete(queue_name)

    yield queue_name

    # Очищаем очередь после каждого теста
    await redis_connection.delete(queue_name)

