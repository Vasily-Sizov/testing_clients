"""
Artemis клиент для работы с очередями.

Переиспользуемый клиент для работы с Artemis, включающий FastAPI роуты и lifecycle управление.
"""

from my_artemis_client.client.client import ArtemisClient
from my_artemis_client.endpoint.base_settings import ArtemisSettings, get_settings
from my_artemis_client.endpoint.lifespan import artemis_lifespan
from my_artemis_client.endpoint.routes import artemis_router

__all__ = [
    "ArtemisClient",
    "artemis_router",
    "artemis_lifespan",
    "ArtemisSettings",
    "get_settings",
]

