from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from redis.asyncio import Redis

from client.client import RedisClient
from client.connection import create_redis_connection
from base_settings import get_settings


@asynccontextmanager
async def redis_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan для подключения роута Redis к FastAPI приложению.

    Создаёт соединение с Redis и RedisClient при старте,
    сохраняет их в app.state, закрывает соединение при остановке.

    Параметры подключения берутся из настроек (base_settings.py).
    """
    settings = get_settings()

    # Создаём соединение
    connection: Redis = create_redis_connection(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
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

    yield

    # Закрываем соединение при остановке
    await connection.aclose()
