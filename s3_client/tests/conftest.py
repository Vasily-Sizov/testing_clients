"""
Общие фикстуры для тестов S3.
"""
import os
import pytest
from aioboto3 import Session

from s3.client import S3Client, create_s3_client


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
def s3_session() -> Session:
    """
    Создаёт сессию S3 для тестов.

    Использует переменные окружения:
    - AWS_ACCESS_KEY_ID
    - AWS_SECRET_ACCESS_KEY
    - AWS_REGION (по умолчанию us-east-1)
    - S3_ENDPOINT_URL (опционально, для совместимых хранилищ)
    """
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", "test")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", "test")
    region_name = os.getenv("AWS_REGION", "us-east-1")
    endpoint_url = os.getenv("S3_ENDPOINT_URL", None)

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
    endpoint_url = os.getenv("S3_ENDPOINT_URL", None)
    use_ssl = os.getenv("S3_USE_SSL", "true").lower() == "true"
    verify = os.getenv("S3_VERIFY", "true").lower() == "true"
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
    endpoint_url = os.getenv("S3_ENDPOINT_URL", None)
    use_ssl = os.getenv("S3_USE_SSL", "true").lower() == "true"
    verify = os.getenv("S3_VERIFY", "true").lower() == "true"
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
    from fastapi import FastAPI
    from s3.routes import router
    from s3.client import S3Client

    app = FastAPI()
    app.include_router(router)

    # Инициализируем клиент напрямую
    endpoint_url = os.getenv("S3_ENDPOINT_URL", None)
    use_ssl = os.getenv("S3_USE_SSL", "true").lower() == "true"
    verify = os.getenv("S3_VERIFY", "true").lower() == "true"
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
    import httpx
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

