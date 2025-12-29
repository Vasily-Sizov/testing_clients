"""
Функции для создания подключений к Artemis.

Аналогично create_opensearch_connection, но для Artemis брокера.
"""

from typing import Optional
from urllib.parse import quote

from my_artemis_client.client.client import ArtemisClient


def create_artemis_connection(
    host: str,
    port: int = 61616,
    username: Optional[str] = None,
    password: Optional[str] = None,
    protocol: str = "amqp",
) -> ArtemisClient:
    """
    Создаёт соединение с Artemis.

    Используется на уровне lifecycle приложения (lifespan).
    Возвращаемый объект должен жить столько же, сколько живёт приложение.

    :param host: хост Artemis брокера
    :param port: порт Artemis брокера (по умолчанию 61616)
    :param username: имя пользователя для аутентификации
    :param password: пароль для аутентификации
    :param protocol: протокол подключения (по умолчанию "amqp")
    :return: ArtemisClient клиент
    """
    # Собираем URL из отдельных параметров
    if username and password:
        # Экранируем username и password для URL (на случай спецсимволов)
        encoded_username = quote(username, safe="")
        encoded_password = quote(password, safe="")
        connection_url = (
            f"{protocol}://{encoded_username}:{encoded_password}@{host}:{port}"
        )
    else:
        connection_url = f"{protocol}://{host}:{port}"

    return ArtemisClient(connection_url)
