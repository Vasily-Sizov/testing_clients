"""
Redis клиент для работы с очередями.

Переиспользуемый клиент для работы с Redis, включающий FastAPI роуты и lifecycle управление.
"""

from client.client import RedisClient
from client.connection import create_redis_connection
from routes import router
from lifespan import redis_lifespan
from base_settings import Settings, get_settings

__all__ = ["RedisClient", "create_redis_connection", "router", "redis_lifespan", "Settings", "get_settings"]
