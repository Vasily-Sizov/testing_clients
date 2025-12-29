"""
Настройки приложения для Redis клиента.

Использует pydantic BaseSettings для загрузки настроек из переменных окружения.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisSettings(BaseSettings):
    """Настройки подключения к Redis."""

    host: str = Field(
        default="localhost", alias="redis_host", description="Хост Redis сервера"
    )
    port: int = Field(
        default=6379, alias="redis_port", description="Порт Redis сервера"
    )
    db: int = Field(default=0, alias="redis_db", description="Номер базы данных (0-15)")
    password: str | None = Field(
        default=None, alias="redis_password", description="Пароль для аутентификации"
    )
    decode_responses: bool = Field(
        default=False,
        alias="redis_decode_responses",
        description="Декодировать ли ответы как строки",
    )
    socket_timeout: float | None = Field(
        default=None,
        alias="redis_socket_timeout",
        description="Таймаут для операций сокета",
    )
    socket_connect_timeout: float | None = Field(
        default=None,
        alias="redis_socket_connect_timeout",
        description="Таймаут для подключения",
    )
    retry_on_timeout: bool = Field(
        default=True,
        alias="redis_retry_on_timeout",
        description="Повторять ли запрос при таймауте",
    )
    health_check_interval: int = Field(
        default=30,
        alias="redis_health_check_interval",
        description="Интервал проверки здоровья соединения",
    )

    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
    )


@lru_cache()
def get_settings() -> RedisSettings:
    """
    Получить настройки приложения.

    Использует @lru_cache для кэширования - настройки загружаются один раз
    и переиспользуются при последующих вызовах.

    :return: экземпляр RedisSettings
    """
    return RedisSettings()
