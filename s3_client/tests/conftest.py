"""
Общие фикстуры для тестов S3.
"""
import os
import asyncio
import pytest
import httpx
from aioboto3 import Session
from fastapi import FastAPI

from my_s3_client.client import S3Client, create_s3_client
from my_s3_client.endpoint.routes import s3_router


@pytest.fixture(scope="module")
def event_loop():
    """
    Создаёт event loop для модуля тестов.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def s3_session() -> Session:
    """
    Создаёт сессию S3 для тестов.

    Использует переменные окружения (если установлены), иначе значения по умолчанию для MinIO:
    - AWS_ACCESS_KEY_ID (по умолчанию: minioadmin)
    - AWS_SECRET_ACCESS_KEY (по умолчанию: minioadmin)
    - AWS_REGION (по умолчанию: us-east-1)
    - AWS_ENDPOINT_URL (по умолчанию: http://localhost:9000 для MinIO)
    """
    # Значения по умолчанию для локального MinIO
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID") or "minioadmin"
    if aws_access_key_id:
        aws_access_key_id = aws_access_key_id.strip()
    
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY") or "minioadmin"
    if aws_secret_access_key:
        aws_secret_access_key = aws_secret_access_key.strip()
    
    region_name = os.getenv("AWS_REGION") or "us-east-1"
    if region_name:
        region_name = region_name.strip()
    
    # По умолчанию используем локальный MinIO
    endpoint_url = os.getenv("AWS_ENDPOINT_URL") or "http://localhost:9000"
    if endpoint_url:
        endpoint_url = endpoint_url.strip()

    session = create_s3_client(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name,
        endpoint_url=endpoint_url,
    )

    return session


@pytest.fixture(scope="module")
def client(s3_session: Session) -> S3Client:
    """
    Создаёт S3Client для тестов клиента напрямую.
    """
    # По умолчанию для MinIO используем http (без SSL)
    endpoint_url = os.getenv("AWS_ENDPOINT_URL") or "http://localhost:9000"
    if endpoint_url:
        endpoint_url = endpoint_url.strip()
    
    # По умолчанию для MinIO: use_ssl=false, verify=false
    use_ssl_str = os.getenv("AWS_USE_SSL", "false")
    use_ssl = use_ssl_str.strip().lower() == "true" if use_ssl_str else False
    
    verify_str = os.getenv("AWS_VERIFY", "false")
    verify = verify_str.strip().lower() == "true" if verify_str else False
    return S3Client(
        session=s3_session,
        endpoint_url=endpoint_url,
        use_ssl=use_ssl,
        verify=verify,
    )


@pytest.fixture(scope="module")
def integration_client(s3_session: Session) -> S3Client:
    """
    Создаёт S3Client для интеграционных тестов API.
    """
    # По умолчанию для MinIO используем http (без SSL)
    endpoint_url = os.getenv("AWS_ENDPOINT_URL") or "http://localhost:9000"
    if endpoint_url:
        endpoint_url = endpoint_url.strip()
    
    # По умолчанию для MinIO: use_ssl=false, verify=false
    use_ssl_str = os.getenv("AWS_USE_SSL", "false")
    use_ssl = use_ssl_str.strip().lower() == "true" if use_ssl_str else False
    
    verify_str = os.getenv("AWS_VERIFY", "false")
    verify = verify_str.strip().lower() == "true" if verify_str else False
    return S3Client(
        session=s3_session,
        endpoint_url=endpoint_url,
        use_ssl=use_ssl,
        verify=verify,
    )


@pytest.fixture(scope="module")
def integration_app(s3_session: Session):
    """
    Создаёт FastAPI приложение для интеграционных тестов API.
    """
    app = FastAPI()
    app.include_router(s3_router)

    # Инициализируем клиент напрямую
    # По умолчанию для MinIO используем http (без SSL)
    endpoint_url = os.getenv("AWS_ENDPOINT_URL") or "http://localhost:9000"
    if endpoint_url:
        endpoint_url = endpoint_url.strip()
    
    # По умолчанию для MinIO: use_ssl=false, verify=false
    use_ssl_str = os.getenv("AWS_USE_SSL", "false")
    use_ssl = use_ssl_str.strip().lower() == "true" if use_ssl_str else False
    
    verify_str = os.getenv("AWS_VERIFY", "false")
    verify = verify_str.strip().lower() == "true" if verify_str else False
    client = S3Client(
        session=s3_session,
        endpoint_url=endpoint_url,
        use_ssl=use_ssl,
        verify=verify,
    )
    app.state.s3_session = s3_session
    app.state.s3_client = client

    return app


@pytest.fixture(scope="module")
async def integration_test_client(integration_app):
    """
    Создаёт httpx.AsyncClient для интеграционных тестов API.
    """
    async with httpx.AsyncClient(app=integration_app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="module")
async def test_bucket(client: S3Client) -> str:
    """
    Создаёт тестовый bucket и удаляет его после тестов.

    :return: имя тестового bucket'а
    """
    bucket_name = "test-bucket-s3"

    # Удаляем bucket, если существует
    if await client.bucket_exists(bucket_name):
        # Сначала удаляем все объекты
        objects = await client.list_objects(bucket_name)
        for obj in objects:
            await client.delete_object(bucket_name, obj["key"])
        await client.delete_bucket(bucket_name)

    # Создаём bucket
    await client.create_bucket(bucket_name)

    yield bucket_name

    # Удаляем bucket после тестов
    if await client.bucket_exists(bucket_name):
        # Сначала удаляем все объекты
        objects = await client.list_objects(bucket_name)
        for obj in objects:
            await client.delete_object(bucket_name, obj["key"])
        await client.delete_bucket(bucket_name)

