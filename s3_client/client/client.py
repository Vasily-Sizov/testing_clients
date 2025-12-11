"""
Клиент-обёртка над S3 для работы с объектами.

Содержит только методы работы с S3.
Не управляет соединением и не знает о lifecycle приложения.
"""
import os
from typing import Optional, BinaryIO, Union
from aioboto3 import Session
from botocore.response import StreamingBody


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
        s3_root: str = "",
    ) -> None:
        """
        Инициализирует клиент готовой сессией S3.

        :param session: aioboto3 Session
        :param endpoint_url: URL эндпоинта (для совместимых с S3 хранилищ)
        :param use_ssl: использовать ли SSL
        :param verify: проверять ли SSL сертификаты
        :param s3_root: корневой префикс для путей на S3
        """
        self._session = session
        self._endpoint_url = endpoint_url
        self._use_ssl = use_ssl
        self._verify = verify
        self._s3_root = s3_root

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
        data: Union[bytes, BinaryIO, str],
        content_type: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> dict[str, str]:
        """
        Загружает объект в S3.

        :param bucket_name: имя bucket'а
        :param object_key: ключ объекта (путь к файлу)
        :param data: данные для загрузки (bytes, BinaryIO или путь к файлу как str)
        :param content_type: MIME-тип содержимого
        :param metadata: дополнительные метаданные
        :return: информация о загруженном объекте
        """
        # Если передан путь к файлу, читаем его
        if isinstance(data, str):
            with open(data, "rb") as f:
                data = f.read()
        # Если передан BinaryIO, читаем его
        elif hasattr(data, 'read'):
            data = data.read()

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

    # ========================================================================
    # Дополнительные методы для совместимости со старым клиентом
    # ========================================================================

    def key(self, *paths: str) -> str:
        """
        Добавляет префикс к пути на S3.

        :param paths: части пути
        :return: Абсолютный путь на S3, включая префикс.
        """
        s3_root = self._s3_root
        if not s3_root:
            from s3_client.base_settings import get_settings
            settings = get_settings()
            s3_root = settings.s3_root or ""
        return "/".join([s3_root, *(p.strip("/") for p in paths)]) if s3_root else "/".join(p.strip("/") for p in paths)

    async def get_stream(
        self,
        bucket_name: str,
        object_key: str,
    ) -> StreamingBody:
        """
        Возвращает поток для чтения файла с S3.

        Полезно для больших файлов, которые не нужно загружать целиком в память.

        :param bucket_name: имя bucket'а
        :param object_key: ключ объекта
        :return: StreamingBody для чтения данных
        :raises Exception: если объект не найден
        """
        async with self._session.client(
            "s3",
            endpoint_url=self._endpoint_url,
            use_ssl=self._use_ssl,
            verify=self._verify,
        ) as s3:
            response = await s3.get_object(Bucket=bucket_name, Key=object_key)
            return response["Body"]

    async def download_object_to_file(
        self,
        bucket_name: str,
        object_key: str,
        file_path: str,
    ) -> dict[str, str]:
        """
        Скачивает объект из S3 и сохраняет в файл.

        Использует потоковое чтение через get_stream() для безопасной работы
        с большими файлами. Файл читается по частям (чанками по 8 КБ) и
        записывается на диск, не загружая весь файл в оперативную память.

        Это делает метод безопасным для файлов любого размера (даже гигабайты),
        в отличие от download_object(), который загружает весь файл в память.

        :param bucket_name: имя bucket'а
        :param object_key: ключ объекта
        :param file_path: путь к файлу для сохранения
        :return: информация о скачивании
        :raises Exception: если объект не найден

        Пример использования:
            # Безопасно для файла 5 ГБ
            await client.download_object_to_file(
                bucket_name="my-bucket",
                object_key="huge-file.zip",
                file_path="/local/path/file.zip"
            )
        """
        # Создаём директорию, если её нет
        dir_path = os.path.dirname(file_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        stream = await self.get_stream(bucket_name, object_key)
        
        # Читаем данные по частям и записываем в файл
        with open(file_path, "wb") as f:
            while True:
                chunk = await stream.read(8192)
                if not chunk:
                    break
                f.write(chunk)

        return {
            "bucket_name": bucket_name,
            "object_key": object_key,
            "file_path": file_path,
            "message": "Object downloaded to file successfully",
        }

    async def upload_object_from_file(
        self,
        bucket_name: str,
        object_key: str,
        file_path: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> dict[str, str]:
        """
        Загружает файл с локальной файловой системы в S3.

        :param bucket_name: имя bucket'а
        :param object_key: ключ объекта (путь к файлу на S3)
        :param file_path: путь к локальному файлу
        :param content_type: MIME-тип содержимого
        :param metadata: дополнительные метаданные
        :return: информация о загруженном объекте
        """
        with open(file_path, "rb") as f:
            data = f.read()

        return await self.upload_object(
            bucket_name=bucket_name,
            object_key=object_key,
            data=data,
            content_type=content_type,
            metadata=metadata,
        )

