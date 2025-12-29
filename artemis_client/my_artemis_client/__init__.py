"""
Переиспользуемый клиент для работы с Artemis очередями.

Основные компоненты:
- ArtemisClient: клиент для работы с Artemis
- create_artemis_connection: функция для создания подключения
- artemis_router: FastAPI роутер с эндпоинтами
- ArtemisSettings: настройки подключения
"""

from my_artemis_client.client import ArtemisClient, create_artemis_connection
from my_artemis_client.endpoint import (
    ArtemisSettings,
    get_settings,
    artemis_lifespan,
    artemis_router,
)

__all__ = [
    "ArtemisClient",
    "create_artemis_connection",
    "artemis_router",
    "artemis_lifespan",
    "ArtemisSettings",
    "get_settings",
]

