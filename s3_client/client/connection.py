from typing import Optional
from aioboto3 import Session


def create_s3_client(
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    region_name: str = "us-east-1",
    endpoint_url: Optional[str] = None,
    use_ssl: bool = True,
    verify: bool = True,
) -> Session:
    """
    Создаёт сессию S3 клиента.

    Используется на уровне lifecycle приложения (lifespan).
    Возвращаемый объект должен жить столько же, сколько живёт приложение.

    :param aws_access_key_id: AWS Access Key ID
    :param aws_secret_access_key: AWS Secret Access Key
    :param region_name: регион AWS (по умолчанию us-east-1)
    :param endpoint_url: URL эндпоинта (для совместимых с S3 хранилищ, например MinIO)
    :param use_ssl: использовать ли SSL
    :param verify: проверять ли SSL сертификаты
    :return: aioboto3 Session
    """
    return Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name,
    )

