"""
Настройки приложения для Redis клиента.

Использует pydantic BaseSettings для загрузки настроек из переменных окружения.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisSettings(BaseSettings):
    """Настройки подключения к Redis."""

    redis_host: str = Field(
        default="localhost", description="Хост Redis сервера"
    )
    redis_port: int = Field(
        default=6379, description="Порт Redis сервера"
    )
    redis_db: int = Field(default=0, description="Номер базы данных (0-15)")
    redis_username: str | None = Field(
        default=None, description="Имя пользователя для ACL (Redis 6.0+)"
    )
    redis_password: str | None = Field(
        default=None, description="Пароль для аутентификации"
    )
    redis_decode_responses: bool = Field(
        default=False,
        description="Декодировать ли ответы как строки",
    )
    redis_socket_timeout: float | None = Field(
        default=None,
        description="Таймаут для операций сокета",
    )
    redis_socket_connect_timeout: float | None = Field(
        default=None,
        description="Таймаут для подключения",
    )
    redis_retry_on_timeout: bool = Field(
        default=True,
        description="Повторять ли запрос при таймауте",
    )
    redis_health_check_interval: int = Field(
        default=30,
        description="Интервал проверки здоровья соединения",
    )

    model_config = SettingsConfigDict(
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
