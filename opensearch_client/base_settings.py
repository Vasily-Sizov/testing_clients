"""
Настройки приложения для OpenSearch клиента.

Использует pydantic BaseSettings для загрузки настроек из переменных окружения.
"""
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки подключения к OpenSearch."""

    opensearch_hosts: str = Field(
        default="http://localhost:9200",
        description="Список хостов OpenSearch (через запятую)",
    )
    opensearch_username: str | None = Field(
        default=None,
        description="Имя пользователя для basic auth",
    )
    opensearch_password: str | None = Field(
        default=None,
        description="Пароль для basic auth",
    )
    opensearch_timeout: int = Field(
        default=30,
        description="Таймаут запросов",
    )
    opensearch_max_retries: int = Field(
        default=3,
        description="Количество повторов",
    )
    opensearch_retry_on_timeout: bool = Field(
        default=True,
        description="Повторять ли запрос при таймауте",
    )
    opensearch_verify_certs: bool = Field(
        default=True,
        description="Проверять ли SSL-сертификаты",
    )

    model_config = SettingsConfigDict(
        env_prefix="OPENSEARCH_",
        case_sensitive=False,
        env_file=".env",
    )

    @property
    def hosts_list(self) -> list[str]:
        """Возвращает список хостов из строки."""
        return [host.strip() for host in self.opensearch_hosts.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """
    Получить настройки приложения.

    Использует @lru_cache для кэширования - настройки загружаются один раз
    и переиспользуются при последующих вызовах.

    :return: экземпляр Settings
    """
    return Settings()

