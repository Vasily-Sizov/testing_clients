from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from aioboto3 import Session

from s3_client.client.client import S3Client
from s3_client.client.connection import create_s3_client
from s3_client.base_settings import get_settings


@asynccontextmanager
async def s3_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan для подключения роута S3 к FastAPI приложению.

    Создаёт сессию S3 и S3Client при старте,
    сохраняет их в app.state.

    Параметры подключения берутся из настроек (base_settings.py).
    """
    settings = get_settings()

    # Создаём сессию
    session: Session = create_s3_client(
        aws_access_key_id=settings.access_key_id,
        aws_secret_access_key=settings.secret_access_key,
        region_name=settings.region,
        endpoint_url=settings.endpoint_url,
        use_ssl=settings.use_ssl,
        verify=settings.verify,
    )

    # Создаём клиент
    client = S3Client(
        session=session,
        endpoint_url=settings.endpoint_url,
        use_ssl=settings.use_ssl,
        verify=settings.verify,
        s3_root=settings.s3_root,
    )

    # Сохраняем в state приложения
    app.state.s3_session = session
    app.state.s3_client = client

    yield

    # Сессия aioboto3 не требует явного закрытия

