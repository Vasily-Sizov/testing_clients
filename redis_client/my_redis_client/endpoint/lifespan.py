import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from redis.asyncio import Redis

from my_redis_client.client.client import RedisClient
from my_redis_client.client.connection import create_redis_connection
from my_redis_client.endpoint.base_settings import get_settings

logger = logging.getLogger("uvicorn")


@asynccontextmanager
async def redis_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan для подключения роута Redis к FastAPI приложению.

    Создаёт соединение с Redis и RedisClient при старте,
    сохраняет их в app.state, закрывает соединение при остановке.

    Параметры подключения берутся из настроек (base_settings.py).
    """
    logger.info("Redis lifespan: Starting initialization...")
    settings = get_settings()
    logger.info(f"Redis lifespan: Connecting to {settings.redis_host}:{settings.redis_port}")

    # Создаём соединение
    connection: Redis = create_redis_connection(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        username=settings.redis_username,
        password=settings.redis_password,
        decode_responses=settings.redis_decode_responses,
        socket_timeout=settings.redis_socket_timeout,
        socket_connect_timeout=settings.redis_socket_connect_timeout,
        retry_on_timeout=settings.redis_retry_on_timeout,
        health_check_interval=settings.redis_health_check_interval,
    )

    # Создаём клиент
    client = RedisClient(connection)

    # Сохраняем в state приложения
    app.state.redis_connection = connection
    app.state.redis_client = client
    logger.info("Redis lifespan: Client initialized and stored in app.state")

    yield

    # Закрываем соединение при остановке
    logger.info("Redis lifespan: Shutting down...")
    await connection.aclose()
    logger.info("Redis lifespan: Connection closed")
