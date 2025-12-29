from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from opensearchpy import AsyncOpenSearch

from my_opensearch_client.client.client import OpenSearchClient
from my_opensearch_client.client.connection import create_opensearch_connection
from my_opensearch_client.endpoint.base_settings import get_opensearch_settings


@asynccontextmanager
async def opensearch_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan для подключения роута OpenSearch к FastAPI приложению.

    Создаёт соединение с OpenSearch и OpenSearchClient при старте,
    сохраняет их в app.state, закрывает соединение при остановке.

    Параметры подключения берутся из настроек (base_settings.py).
    """
    settings = get_opensearch_settings()

    # Создаём соединение
    connection: AsyncOpenSearch = create_opensearch_connection(
        hosts=settings.hosts_list,
        username=settings.opensearch_username,
        password=settings.opensearch_password,
        timeout=settings.opensearch_timeout,
        max_retries=settings.opensearch_max_retries,
        retry_on_timeout=settings.opensearch_retry_on_timeout,
        verify_certs=settings.opensearch_verify_certs,
    )

    # Создаём клиент
    client = OpenSearchClient(connection)

    # Сохраняем в state приложения
    app.state.opensearch_connection = connection
    app.state.opensearch_client = client

    yield

    # Закрываем соединение при остановке
    await connection.close()

