"""
S3 клиент для работы с объектным хранилищем.

Переиспользуемый клиент для работы с S3, включающий FastAPI роуты и lifecycle управление.
"""

from s3.client import S3Client, create_s3_client
from s3.routes import router
from s3.lifespan import s3_lifespan

__all__ = ["S3Client", "create_s3_client", "router", "s3_lifespan"]

