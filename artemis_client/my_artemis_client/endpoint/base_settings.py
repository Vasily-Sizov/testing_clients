"""
Настройки приложения для Artemis клиента.

Использует pydantic BaseSettings для загрузки настроек из переменных окружения.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ArtemisSettings(BaseSettings):
    """Настройки подключения к Artemis."""

    host: str = Field(
        default="localhost",
        alias="artemis_host",
        description="Хост Artemis брокера",
    )
    port: int = Field(
        default=61616,
        alias="artemis_port",
        description="Порт Artemis брокера",
    )
    username: str | None = Field(
        default=None,
        alias="artemis_username",
        description="Имя пользователя для аутентификации",
    )
    password: str | None = Field(
        default=None,
        alias="artemis_password",
        description="Пароль для аутентификации",
    )
    protocol: str = Field(
        default="amqp",
        alias="artemis_protocol",
        description="Протокол подключения (amqp, amqps)",
    )

    model_config = SettingsConfigDict(
        env_prefix="ARTEMIS_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
    )


@lru_cache()
def get_settings() -> ArtemisSettings:
    """
    Получить настройки приложения.

    Использует @lru_cache для кэширования - настройки загружаются один раз
    и переиспользуются при последующих вызовах.

    :return: экземпляр ArtemisSettings
    """
    return ArtemisSettings()

