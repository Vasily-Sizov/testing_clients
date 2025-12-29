import os
from unittest.mock import AsyncMock
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient
from opensearchpy import AsyncOpenSearch

from my_opensearch_client.client.client import OpenSearchClient
from my_opensearch_client.client.connection import create_opensearch_connection
from my_opensearch_client.endpoint.routes import opensearch_router


# Фикстуры для unit-тестов (с моками)
@pytest.fixture
def mock_client() -> OpenSearchClient:
    """Создаёт мок OpenSearchClient."""
    client = AsyncMock(spec=OpenSearchClient)
    return client


@pytest.fixture
def app(mock_client: OpenSearchClient) -> FastAPI:
    """Создаёт тестовое FastAPI приложение с мок-клиентом."""
    app = FastAPI()
    app.include_router(opensearch_router)
    
    # Сохраняем мок-клиент в state
    app.state.opensearch_client = mock_client
    
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Создаёт TestClient для тестирования API."""
    return TestClient(app)


# Фикстуры для интеграционных тестов (с реальным OpenSearch)
@pytest.fixture(scope="module")
def event_loop():
    """Создаёт event loop с module scope для async фикстур."""
    import asyncio
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def opensearch_connection(event_loop) -> AsyncOpenSearch:
    """
    Создаёт реальное соединение с OpenSearch для интеграционных тестов.
    
    Использует переменные окружения или значения по умолчанию.
    """
    import asyncio
    # Устанавливаем event loop
    asyncio.set_event_loop(event_loop)
    
    hosts = [h.strip() for h in os.getenv("OPENSEARCH_HOSTS", "http://localhost:9200").split(",")]
    username = os.getenv("OPENSEARCH_USERNAME")
    password = os.getenv("OPENSEARCH_PASSWORD")

    connection = create_opensearch_connection(
        hosts=hosts,
        username=username,
        password=password,
        verify_certs=False,
    )

    yield connection

    await connection.close()


@pytest.fixture(scope="module")
async def integration_client(opensearch_connection: AsyncOpenSearch, event_loop) -> OpenSearchClient:
    """Создаёт реальный OpenSearchClient для интеграционных тестов API."""
    import asyncio
    asyncio.set_event_loop(event_loop)
    return OpenSearchClient(opensearch_connection)


@pytest.fixture(scope="module")
async def client(opensearch_connection: AsyncOpenSearch, event_loop) -> OpenSearchClient:
    """Создаёт клиент с реальным соединением для test_integration.py."""
    import asyncio
    asyncio.set_event_loop(event_loop)
    return OpenSearchClient(opensearch_connection)


@pytest.fixture(scope="module")
async def integration_app(integration_client: OpenSearchClient, event_loop) -> FastAPI:
    """Создаёт FastAPI приложение с реальным OpenSearch клиентом."""
    import asyncio
    asyncio.set_event_loop(event_loop)
    
    app = FastAPI()
    app.include_router(opensearch_router)
    app.state.opensearch_client = integration_client
    return app


@pytest.fixture(scope="module")
async def integration_test_client(integration_app: FastAPI, event_loop) -> AsyncClient:
    """
    Создаёт AsyncClient для интеграционных тестов API.
    
    Использует httpx.AsyncClient для правильной работы с async приложением.
    TestClient не подходит, так как создает свой event loop.
    """
    import asyncio
    asyncio.set_event_loop(event_loop)
    
    async with AsyncClient(app=integration_app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="module")
async def api_test_index(opensearch_connection: AsyncOpenSearch, event_loop) -> str:
    """
    Создаёт тестовый индекс для интеграционных тестов API.
    
    :return: имя тестового индекса
    """
    index_name = "test-api-integration-index"

    # Удаляем индекс, если существует
    if await opensearch_connection.indices.exists(index=index_name):
        await opensearch_connection.indices.delete(index=index_name)

    # Создаём индекс с поддержкой kNN
    await opensearch_connection.indices.create(
        index=index_name,
        body={
            "settings": {
                "index": {
                    "knn": True,
                },
            },
            "mappings": {
                "properties": {
                    "title": {"type": "text"},
                    "content": {"type": "text"},
                    "status": {"type": "keyword"},
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": 3,
                    },
                },
            },
        },
    )

    yield index_name

    # Удаляем индекс после тестов
    if await opensearch_connection.indices.exists(index=index_name):
        await opensearch_connection.indices.delete(index=index_name)