"""
Настройки приложения для S3 клиента.

Использует pydantic BaseSettings для загрузки настроек из переменных окружения.
"""
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки подключения к S3."""

    aws_access_key_id: str | None = Field(
        default=None,
        description="AWS Access Key ID",
    )
    aws_secret_access_key: str | None = Field(
        default=None,
        description="AWS Secret Access Key",
    )
    aws_region: str = Field(
        default="us-east-1",
        description="Регион AWS",
    )
    aws_endpoint_url: str | None = Field(
        default=None,
        description="URL эндпоинта (для совместимых с S3 хранилищ)",
    )
    aws_use_ssl: bool = Field(
        default=True,
        description="Использовать ли SSL",
    )
    aws_verify: bool = Field(
        default=True,
        description="Проверять ли SSL сертификаты",
    )

    model_config = SettingsConfigDict(
        env_prefix="AWS_",
        case_sensitive=False,
        env_file=".env",
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Получить настройки приложения.

    Использует @lru_cache для кэширования - настройки загружаются один раз
    и переиспользуются при последующих вызовах.

    :return: экземпляр Settings
    """
    return Settings()

