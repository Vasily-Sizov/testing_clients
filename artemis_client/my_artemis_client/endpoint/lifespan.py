from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from fastapi import FastAPI

from my_artemis_client.client.connection import create_artemis_connection
from my_artemis_client.endpoint.base_settings import get_settings


@asynccontextmanager
async def artemis_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan для подключения роута Artemis к FastAPI приложению.

    Создаёт ArtemisClient при старте,
    сохраняет его в app.state.

    Параметры подключения берутся из настроек (base_settings.py).
    """
    logger = logging.getLogger("uvicorn")
    
    logger.info("Artemis lifespan: Starting initialization...")
    settings = get_settings()
    
    # Создаём клиент используя отдельные параметры
    client = create_artemis_connection(
        host=settings.host,
        port=settings.port,
        username=settings.username,
        password=settings.password,
        protocol=settings.protocol,
    )
    logger.info(
        f"Artemis lifespan: Connecting to Artemis at {settings.host}:{settings.port}"
    )

    # Сохраняем в state приложения
    app.state.artemis_client = client
    logger.info("Artemis lifespan: Client initialized and stored in app.state")

    yield

    # Закрытие не требуется, т.к. каждое соединение создаётся на время отправки
    logger.info("Artemis lifespan: Shutting down...")

