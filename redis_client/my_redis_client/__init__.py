"""
Переиспользуемый клиент для работы с Redis очередями.

Основные компоненты:
- RedisClient: клиент для работы с Redis
- redis_router: FastAPI роутер с эндпоинтами
- RedisSettings: настройки подключения
"""

from my_redis_client.client import RedisClient, create_redis_connection
from my_redis_client.endpoint import (
    RedisSettings,
    get_settings,
    redis_lifespan,
    redis_router,
)

__all__ = [
    "RedisClient",
    "create_redis_connection",
    "redis_router",
    "redis_lifespan",
    "RedisSettings",
    "get_settings",
]
