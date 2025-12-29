"""
S3 клиент для работы с объектным хранилищем.

Переиспользуемый клиент для работы с S3, включающий FastAPI роуты и lifecycle управление.
"""

from my_s3_client.client import S3Client, create_s3_client
from my_s3_client.endpoint.routes import s3_router
from my_s3_client.endpoint.lifespan import s3_lifespan

__all__ = ["S3Client", "create_s3_client", "s3_router", "s3_lifespan"]

