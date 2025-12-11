"""
Модели данных для API запросов S3.

Содержит Pydantic модели для валидации входящих запросов.
"""
from typing import Optional
from pydantic import BaseModel, Field


class UploadObjectRequest(BaseModel):
    """
    Запрос на загрузку объекта в S3.

    :param bucket_name: имя bucket'а
    :param object_key: ключ объекта (путь к файлу)
    :param data: данные для загрузки (base64 строка)
    :param content_type: MIME-тип содержимого
    :param metadata: дополнительные метаданные
    """

    bucket_name: str = Field(..., description="Имя bucket'а")
    object_key: str = Field(..., description="Ключ объекта (путь к файлу)")
    data: str = Field(..., description="Данные для загрузки (base64 строка)")
    content_type: Optional[str] = Field(None, description="MIME-тип содержимого")
    metadata: Optional[dict[str, str]] = Field(None, description="Дополнительные метаданные")


class DownloadObjectRequest(BaseModel):
    """
    Запрос на скачивание объекта из S3.

    :param bucket_name: имя bucket'а
    :param object_key: ключ объекта
    """

    bucket_name: str = Field(..., description="Имя bucket'а")
    object_key: str = Field(..., description="Ключ объекта")


class DeleteObjectRequest(BaseModel):
    """
    Запрос на удаление объекта из S3.

    :param bucket_name: имя bucket'а
    :param object_key: ключ объекта
    """

    bucket_name: str = Field(..., description="Имя bucket'а")
    object_key: str = Field(..., description="Ключ объекта")


class ObjectExistsRequest(BaseModel):
    """
    Запрос на проверку существования объекта.

    :param bucket_name: имя bucket'а
    :param object_key: ключ объекта
    """

    bucket_name: str = Field(..., description="Имя bucket'а")
    object_key: str = Field(..., description="Ключ объекта")


class ListObjectsRequest(BaseModel):
    """
    Запрос на получение списка объектов в bucket'е.

    :param bucket_name: имя bucket'а
    :param prefix: префикс для фильтрации объектов
    :param max_keys: максимальное количество объектов для возврата
    """

    bucket_name: str = Field(..., description="Имя bucket'а")
    prefix: str = Field("", description="Префикс для фильтрации")
    max_keys: int = Field(1000, ge=1, le=10000, description="Максимальное количество объектов")


class GetObjectMetadataRequest(BaseModel):
    """
    Запрос на получение метаданных объекта.

    :param bucket_name: имя bucket'а
    :param object_key: ключ объекта
    """

    bucket_name: str = Field(..., description="Имя bucket'а")
    object_key: str = Field(..., description="Ключ объекта")


class CopyObjectRequest(BaseModel):
    """
    Запрос на копирование объекта в S3.

    :param source_bucket: исходный bucket
    :param source_key: исходный ключ объекта
    :param dest_bucket: целевой bucket
    :param dest_key: целевой ключ объекта
    """

    source_bucket: str = Field(..., description="Исходный bucket")
    source_key: str = Field(..., description="Исходный ключ объекта")
    dest_bucket: str = Field(..., description="Целевой bucket")
    dest_key: str = Field(..., description="Целевой ключ объекта")


class GeneratePresignedUrlRequest(BaseModel):
    """
    Запрос на генерацию presigned URL для доступа к объекту.

    :param bucket_name: имя bucket'а
    :param object_key: ключ объекта
    :param expiration: время жизни URL в секундах
    :param method: метод доступа ('get_object' или 'put_object')
    """

    bucket_name: str = Field(..., description="Имя bucket'а")
    object_key: str = Field(..., description="Ключ объекта")
    expiration: int = Field(3600, ge=1, le=604800, description="Время жизни URL в секундах")
    method: str = Field("get_object", pattern="^(get_object|put_object)$", description="Метод доступа")


class CreateBucketRequest(BaseModel):
    """
    Запрос на создание bucket'а.

    :param bucket_name: имя bucket'а
    :param region: регион для создания bucket'а
    """

    bucket_name: str = Field(..., description="Имя bucket'а")
    region: Optional[str] = Field(None, description="Регион для создания bucket'а")


class DeleteBucketRequest(BaseModel):
    """
    Запрос на удаление bucket'а.

    :param bucket_name: имя bucket'а
    """

    bucket_name: str = Field(..., description="Имя bucket'а")

