"""
Redis клиент для работы с очередями.

Переиспользуемый клиент для работы с Redis, включающий FastAPI роуты и lifecycle управление.
"""

from my_redis_client.client.client import RedisClient
from my_redis_client.client.connection import create_redis_connection
from my_redis_client.endpoint.base_settings import RedisSettings, get_settings
from my_redis_client.endpoint.lifespan import redis_lifespan
from my_redis_client.endpoint.routes import redis_router

__all__ = [
    "RedisClient",
    "create_redis_connection",
    "redis_router",
    "redis_lifespan",
    "RedisSettings",
    "get_settings",
]
