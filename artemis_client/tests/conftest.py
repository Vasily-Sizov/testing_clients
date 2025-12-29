"""
Общие фикстуры для тестов Artemis.
"""

import asyncio

import httpx
import pytest
from fastapi import FastAPI

from my_artemis_client.client.client import ArtemisClient
from my_artemis_client.client.connection import create_artemis_connection
from my_artemis_client.endpoint.base_settings import get_settings


@pytest.fixture(scope="module")
def event_loop():
    """
    Создаёт event loop для модуля тестов.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def artemis_client() -> ArtemisClient:
    """
    Создаёт ArtemisClient для тестов.

    Использует настройки из base_settings.py.
    """
    settings = get_settings()
    return create_artemis_connection(
        host=settings.host,
        port=settings.port,
        username=settings.username,
        password=settings.password,
        protocol=settings.protocol,
    )


@pytest.fixture(scope="module")
def client(artemis_client: ArtemisClient) -> ArtemisClient:
    """
    Создаёт ArtemisClient для тестов клиента напрямую.
    """
    return artemis_client


@pytest.fixture(scope="module")
def integration_client(artemis_client: ArtemisClient) -> ArtemisClient:
    """
    Создаёт ArtemisClient для интеграционных тестов API.
    """
    return artemis_client


@pytest.fixture(scope="module")
def integration_app(artemis_client: ArtemisClient):
    """
    Создаёт FastAPI приложение для интеграционных тестов API.
    """
    from my_artemis_client.client.client import ArtemisClient
    from my_artemis_client.endpoint.routes import artemis_router

    app = FastAPI()
    app.include_router(artemis_router)

    # Инициализируем клиент напрямую
    app.state.artemis_client = artemis_client

    return app


@pytest.fixture(scope="module")
async def integration_test_client(integration_app):
    """
    Создаёт httpx.AsyncClient для интеграционных тестов API.
    """
    async with httpx.AsyncClient(app=integration_app, base_url="http://test") as client:
        yield client


@pytest.fixture
def test_queue() -> str:
    """
    Возвращает имя тестовой очереди.

    :return: имя тестовой очереди
    """
    return "test-queue"

