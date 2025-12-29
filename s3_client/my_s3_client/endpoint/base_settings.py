"""
Настройки приложения для S3 клиента.

Использует pydantic BaseSettings для загрузки настроек из переменных окружения.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class S3Settings(BaseSettings):
    """Настройки подключения к S3."""

    access_key_id: str | None = Field(
        default=None,
        description="AWS Access Key ID",
        alias="aws_access_key_id",
    )
    secret_access_key: str | None = Field(
        default=None,
        description="AWS Secret Access Key",
        alias="aws_secret_access_key",
    )
    region: str = Field(
        default="us-east-1",
        description="Регион AWS",
        alias="aws_region",
    )
    endpoint_url: str | None = Field(
        default=None,
        description="URL эндпоинта (для совместимых с S3 хранилищ)",
        alias="aws_endpoint_url",
    )
    use_ssl: bool = Field(
        default=True,
        description="Использовать ли SSL",
        alias="aws_use_ssl",
    )
    verify: bool = Field(
        default=True,
        description="Проверять ли SSL сертификаты",
        alias="aws_verify",
    )
    s3_root: str = Field(
        default="",
        description="Корневой префикс для путей на S3",
        alias="aws_s3_root",
    )

    model_config = SettingsConfigDict(
        env_prefix="AWS_",
        case_sensitive=False,
        env_file=".env",
        populate_by_name=True,  # Позволяет использовать и alias и реальные имена
    )


@lru_cache()
def get_settings() -> S3Settings:
    """
    Получить настройки приложения.

    Использует @lru_cache для кэширования - настройки загружаются один раз
    и переиспользуются при последующих вызовах.

    :return: экземпляр S3Settings
    """
    return S3Settings()
