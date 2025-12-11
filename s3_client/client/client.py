"""
Клиент-обёртка над S3 для работы с объектами.

Содержит только методы работы с S3.
Не управляет соединением и не знает о lifecycle приложения.
"""
from typing import Optional, BinaryIO, AsyncIterator
from io import BytesIO
from aioboto3 import Session


class S3Client:
    """
    Клиент-обёртка над S3 для работы с объектами.

    Содержит только методы работы с S3.
    Не управляет соединением и не знает о lifecycle приложения.
    """

    def __init__(
        self,
        session: Session,
        endpoint_url: Optional[str] = None,
        use_ssl: bool = True,
        verify: bool = True,
    ) -> None:
        """
        Инициализирует клиент готовой сессией S3.

        :param session: aioboto3 Session
        :param endpoint_url: URL эндпоинта (для совместимых с S3 хранилищ)
        :param use_ssl: использовать ли SSL
        :param verify: проверять ли SSL сертификаты
        """
        self._session = session
        self._endpoint_url = endpoint_url
        self._use_ssl = use_ssl
        self._verify = verify

    async def ping(self) -> bool:
        """
        Проверяет доступность S3.

        :return: True, если S3 доступен
        """
        try:
            async with self._session.client(
                "s3",
                endpoint_url=self._endpoint_url,
                use_ssl=self._use_ssl,
                verify=self._verify,
            ) as s3:
                await s3.list_buckets()
            return True
        except Exception:
            return False

    async def list_buckets(self) -> list[dict[str, str]]:
        """
        Возвращает список всех bucket'ов.

        :return: список словарей с информацией о bucket'ах
        """
        async with self._session.client(
            "s3",
            endpoint_url=self._endpoint_url,
            use_ssl=self._use_ssl,
            verify=self._verify,
        ) as s3:
            response = await s3.list_buckets()
            buckets = []
            for bucket in response.get("Buckets", []):
                buckets.append({
                    "name": bucket["Name"],
                    "creation_date": bucket["CreationDate"].isoformat() if bucket.get("CreationDate") else None,
                })
            return buckets

    async def bucket_exists(self, bucket_name: str) -> bool:
        """
        Проверяет существование bucket'а.

        :param bucket_name: имя bucket'а
        :return: True, если bucket существует
        """
        try:
            async with self._session.client(
                "s3",
                endpoint_url=self._endpoint_url,
                use_ssl=self._use_ssl,
                verify=self._verify,
            ) as s3:
                await s3.head_bucket(Bucket=bucket_name)
            return True
        except Exception:
            return False

    async def create_bucket(self, bucket_name: str, region: Optional[str] = None) -> dict[str, str]:
        """
        Создаёт bucket.

        :param bucket_name: имя bucket'а
        :param region: регион для создания bucket'а
        :return: информация о созданном bucket'е
        """
        async with self._session.client(
            "s3",
            endpoint_url=self._endpoint_url,
            use_ssl=self._use_ssl,
            verify=self._verify,
        ) as s3:
            if region and region != "us-east-1":
                await s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={"LocationConstraint": region},
                )
            else:
                await s3.create_bucket(Bucket=bucket_name)

            return {
                "bucket_name": bucket_name,
                "message": "Bucket created successfully",
            }

    async def delete_bucket(self, bucket_name: str) -> dict[str, str]:
        """
        Удаляет bucket (только если он пуст).

        :param bucket_name: имя bucket'а
        :return: информация об удалении
        """
        async with self._session.client(
            "s3",
            endpoint_url=self._endpoint_url,
            use_ssl=self._use_ssl,
            verify=self._verify,
        ) as s3:
            await s3.delete_bucket(Bucket=bucket_name)
            return {
                "bucket_name": bucket_name,
                "message": "Bucket deleted successfully",
            }

    # ========================================================================
    # Методы для работы с объектами
    # ========================================================================

    async def upload_object(
        self,
        bucket_name: str,
        object_key: str,
        data: bytes,
        content_type: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> dict[str, str]:
        """
        Загружает объект в S3.

        :param bucket_name: имя bucket'а
        :param object_key: ключ объекта (путь к файлу)
        :param data: данные для загрузки (bytes)
        :param content_type: MIME-тип содержимого
        :param metadata: дополнительные метаданные
        :return: информация о загруженном объекте
        """
        async with self._session.client(
            "s3",
            endpoint_url=self._endpoint_url,
            use_ssl=self._use_ssl,
            verify=self._verify,
        ) as s3:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type
            if metadata:
                extra_args["Metadata"] = metadata

            await s3.put_object(
                Bucket=bucket_name,
                Key=object_key,
                Body=data,
                **extra_args,
            )

            return {
                "bucket_name": bucket_name,
                "object_key": object_key,
                "message": "Object uploaded successfully",
            }

    async def download_object(
        self,
        bucket_name: str,
        object_key: str,
    ) -> bytes:
        """
        Скачивает объект из S3.

        :param bucket_name: имя bucket'а
        :param object_key: ключ объекта
        :return: данные объекта (bytes)
        :raises Exception: если объект не найден
        """
        async with self._session.client(
            "s3",
            endpoint_url=self._endpoint_url,
            use_ssl=self._use_ssl,
            verify=self._verify,
        ) as s3:
            response = await s3.get_object(Bucket=bucket_name, Key=object_key)
            data = await response["Body"].read()
            return data

    async def delete_object(
        self,
        bucket_name: str,
        object_key: str,
    ) -> dict[str, str]:
        """
        Удаляет объект из S3.

        :param bucket_name: имя bucket'а
        :param object_key: ключ объекта
        :return: информация об удалении
        """
        async with self._session.client(
            "s3",
            endpoint_url=self._endpoint_url,
            use_ssl=self._use_ssl,
            verify=self._verify,
        ) as s3:
            await s3.delete_object(Bucket=bucket_name, Key=object_key)
            return {
                "bucket_name": bucket_name,
                "object_key": object_key,
                "message": "Object deleted successfully",
            }

    async def object_exists(
        self,
        bucket_name: str,
        object_key: str,
    ) -> bool:
        """
        Проверяет существование объекта.

        :param bucket_name: имя bucket'а
        :param object_key: ключ объекта
        :return: True, если объект существует
        """
        try:
            async with self._session.client(
                "s3",
                endpoint_url=self._endpoint_url,
                use_ssl=self._use_ssl,
                verify=self._verify,
            ) as s3:
                await s3.head_object(Bucket=bucket_name, Key=object_key)
            return True
        except Exception:
            return False

    async def list_objects(
        self,
        bucket_name: str,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> list[dict[str, any]]:
        """
        Возвращает список объектов в bucket'е.

        :param bucket_name: имя bucket'а
        :param prefix: префикс для фильтрации объектов
        :param max_keys: максимальное количество объектов для возврата
        :return: список объектов с информацией
        """
        async with self._session.client(
            "s3",
            endpoint_url=self._endpoint_url,
            use_ssl=self._use_ssl,
            verify=self._verify,
        ) as s3:
            response = await s3.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys,
            )

            objects = []
            for obj in response.get("Contents", []):
                objects.append({
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"].isoformat() if obj.get("LastModified") else None,
                    "etag": obj.get("ETag", "").strip('"'),
                })

            return objects

    async def get_object_metadata(
        self,
        bucket_name: str,
        object_key: str,
    ) -> dict[str, any]:
        """
        Возвращает метаданные объекта.

        :param bucket_name: имя bucket'а
        :param object_key: ключ объекта
        :return: метаданные объекта
        """
        async with self._session.client(
            "s3",
            endpoint_url=self._endpoint_url,
            use_ssl=self._use_ssl,
            verify=self._verify,
        ) as s3:
            response = await s3.head_object(Bucket=bucket_name, Key=object_key)
            return {
                "key": object_key,
                "size": response.get("ContentLength", 0),
                "content_type": response.get("ContentType", ""),
                "last_modified": response.get("LastModified").isoformat() if response.get("LastModified") else None,
                "etag": response.get("ETag", "").strip('"'),
                "metadata": response.get("Metadata", {}),
            }

    async def copy_object(
        self,
        source_bucket: str,
        source_key: str,
        dest_bucket: str,
        dest_key: str,
    ) -> dict[str, str]:
        """
        Копирует объект в S3.

        :param source_bucket: исходный bucket
        :param source_key: исходный ключ объекта
        :param dest_bucket: целевой bucket
        :param dest_key: целевой ключ объекта
        :return: информация о копировании
        """
        async with self._session.client(
            "s3",
            endpoint_url=self._endpoint_url,
            use_ssl=self._use_ssl,
            verify=self._verify,
        ) as s3:
            copy_source = {
                "Bucket": source_bucket,
                "Key": source_key,
            }
            await s3.copy_object(
                CopySource=copy_source,
                Bucket=dest_bucket,
                Key=dest_key,
            )

            return {
                "source_bucket": source_bucket,
                "source_key": source_key,
                "dest_bucket": dest_bucket,
                "dest_key": dest_key,
                "message": "Object copied successfully",
            }

    async def generate_presigned_url(
        self,
        bucket_name: str,
        object_key: str,
        expiration: int = 3600,
        method: str = "get_object",
    ) -> str:
        """
        Генерирует presigned URL для доступа к объекту.

        :param bucket_name: имя bucket'а
        :param object_key: ключ объекта
        :param expiration: время жизни URL в секундах (по умолчанию 1 час)
        :param method: метод доступа ('get_object' или 'put_object')
        :return: presigned URL
        """
        async with self._session.client(
            "s3",
            endpoint_url=self._endpoint_url,
            use_ssl=self._use_ssl,
            verify=self._verify,
        ) as s3:
            url = await s3.generate_presigned_url(
                ClientMethod=method,
                Params={
                    "Bucket": bucket_name,
                    "Key": object_key,
                },
                ExpiresIn=expiration,
            )
            return url

