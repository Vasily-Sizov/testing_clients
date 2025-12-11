"""
Интеграционные тесты с реальным S3.

Требуют запущенный S3 (например, MinIO через docker-compose).
Эти тесты проверяют:
1. Работу клиента S3Client напрямую
2. Работу API роутов через HTTP
"""
import os
import base64
import tempfile
import pytest
from pathlib import Path
from httpx import AsyncClient

from s3_client.client import S3Client
from s3_client.client.utils import sync_dir


# ============================================================================
# Тесты API роутов
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
class TestPing:
    """Тесты для эндпоинта /ping."""

    async def test_ping_success(self, integration_test_client: AsyncClient) -> None:
        """Тест успешного ping с реальным S3."""
        response = await integration_test_client.get("/s3/ping")

        assert response.status_code == 200
        assert response.json() == {"available": True}


@pytest.mark.integration
@pytest.mark.asyncio
class TestListBuckets:
    """Тесты для эндпоинта /buckets."""

    async def test_list_buckets_success(
        self,
        integration_test_client: AsyncClient,
        test_bucket: str,
    ) -> None:
        """Тест получения списка bucket'ов."""
        response = await integration_test_client.get("/s3/buckets")

        assert response.status_code == 200
        buckets = response.json()
        assert isinstance(buckets, list)
        bucket_names = [b["name"] for b in buckets]
        assert test_bucket in bucket_names


@pytest.mark.integration
@pytest.mark.asyncio
class TestBucketExists:
    """Тесты для эндпоинта /buckets/exists."""

    async def test_bucket_exists_true(
        self,
        integration_test_client: AsyncClient,
        test_bucket: str,
    ) -> None:
        """Тест существующего bucket'а."""
        response = await integration_test_client.post(
            f"/s3/buckets/exists?bucket_name={test_bucket}"
        )

        assert response.status_code == 200
        assert response.json()["exists"] is True

    async def test_bucket_exists_false(
        self,
        integration_test_client: AsyncClient,
    ) -> None:
        """Тест несуществующего bucket'а."""
        response = await integration_test_client.post(
            "/s3/buckets/exists?bucket_name=non-existent-bucket"
        )

        assert response.status_code == 200
        assert response.json()["exists"] is False


# ============================================================================
# Тесты для работы с объектами через API
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
class TestUploadObject:
    """Тесты для эндпоинта /objects/upload."""

    async def test_upload_success(
        self,
        integration_test_client: AsyncClient,
        test_bucket: str,
    ) -> None:
        """Тест успешной загрузки объекта."""
        test_data = b"test file content"
        data_base64 = base64.b64encode(test_data).decode("utf-8")

        response = await integration_test_client.post(
            "/s3/objects/upload",
            json={
                "bucket_name": test_bucket,
                "object_key": "test-file.txt",
                "data": data_base64,
                "content_type": "text/plain",
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["bucket_name"] == test_bucket
        assert result["object_key"] == "test-file.txt"


@pytest.mark.integration
@pytest.mark.asyncio
class TestDownloadObject:
    """Тесты для эндпоинта /objects/download."""

    async def test_download_success(
        self,
        integration_test_client: AsyncClient,
        test_bucket: str,
    ) -> None:
        """Тест успешного скачивания объекта."""
        # Сначала загружаем объект
        test_data = b"test download content"
        data_base64 = base64.b64encode(test_data).decode("utf-8")

        await integration_test_client.post(
            "/s3/objects/upload",
            json={
                "bucket_name": test_bucket,
                "object_key": "download-test.txt",
                "data": data_base64,
            },
        )

        # Скачиваем объект
        response = await integration_test_client.post(
            "/s3/objects/download",
            json={
                "bucket_name": test_bucket,
                "object_key": "download-test.txt",
            },
        )

        assert response.status_code == 200
        assert response.content == test_data

    async def test_download_not_found(
        self,
        integration_test_client: AsyncClient,
        test_bucket: str,
    ) -> None:
        """Тест скачивания несуществующего объекта."""
        response = await integration_test_client.post(
            "/s3/objects/download",
            json={
                "bucket_name": test_bucket,
                "object_key": "non-existent-file.txt",
            },
        )

        assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
class TestDeleteObject:
    """Тесты для эндпоинта /objects/delete."""

    async def test_delete_success(
        self,
        integration_test_client: AsyncClient,
        test_bucket: str,
    ) -> None:
        """Тест успешного удаления объекта."""
        # Сначала загружаем объект
        test_data = b"test delete content"
        data_base64 = base64.b64encode(test_data).decode("utf-8")

        await integration_test_client.post(
            "/s3/objects/upload",
            json={
                "bucket_name": test_bucket,
                "object_key": "delete-test.txt",
                "data": data_base64,
            },
        )

        # Удаляем объект
        response = await integration_test_client.post(
            "/s3/objects/delete",
            json={
                "bucket_name": test_bucket,
                "object_key": "delete-test.txt",
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["bucket_name"] == test_bucket
        assert result["object_key"] == "delete-test.txt"


@pytest.mark.integration
@pytest.mark.asyncio
class TestObjectExists:
    """Тесты для эндпоинта /objects/exists."""

    async def test_object_exists_true(
        self,
        integration_test_client: AsyncClient,
        test_bucket: str,
    ) -> None:
        """Тест существующего объекта."""
        # Сначала загружаем объект
        test_data = b"test exists content"
        data_base64 = base64.b64encode(test_data).decode("utf-8")

        await integration_test_client.post(
            "/s3/objects/upload",
            json={
                "bucket_name": test_bucket,
                "object_key": "exists-test.txt",
                "data": data_base64,
            },
        )

        response = await integration_test_client.post(
            "/s3/objects/exists",
            json={
                "bucket_name": test_bucket,
                "object_key": "exists-test.txt",
            },
        )

        assert response.status_code == 200
        assert response.json()["exists"] is True

    async def test_object_exists_false(
        self,
        integration_test_client: AsyncClient,
        test_bucket: str,
    ) -> None:
        """Тест несуществующего объекта."""
        response = await integration_test_client.post(
            "/s3/objects/exists",
            json={
                "bucket_name": test_bucket,
                "object_key": "non-existent-file.txt",
            },
        )

        assert response.status_code == 200
        assert response.json()["exists"] is False


@pytest.mark.integration
@pytest.mark.asyncio
class TestListObjects:
    """Тесты для эндпоинта /objects/list."""

    async def test_list_objects_success(
        self,
        integration_test_client: AsyncClient,
        test_bucket: str,
    ) -> None:
        """Тест получения списка объектов."""
        # Загружаем несколько объектов
        for i in range(3):
            test_data = f"test content {i}".encode()
            data_base64 = base64.b64encode(test_data).decode("utf-8")

            await integration_test_client.post(
                "/s3/objects/upload",
                json={
                    "bucket_name": test_bucket,
                    "object_key": f"test-file-{i}.txt",
                    "data": data_base64,
                },
            )

        response = await integration_test_client.post(
            "/s3/objects/list",
            json={
                "bucket_name": test_bucket,
                "prefix": "test-file-",
                "max_keys": 100,
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["bucket_name"] == test_bucket
        assert len(result["objects"]) == 3
        # Проверяем, что все созданные объекты присутствуют
        object_keys = [obj["key"] for obj in result["objects"]]
        for i in range(3):
            assert f"test-file-{i}.txt" in object_keys


@pytest.mark.integration
@pytest.mark.asyncio
class TestGetObjectMetadata:
    """Тесты для эндпоинта /objects/metadata."""

    async def test_get_metadata_success(
        self,
        integration_test_client: AsyncClient,
        test_bucket: str,
    ) -> None:
        """Тест получения метаданных объекта."""
        # Загружаем объект
        test_data = b"test metadata content"
        data_base64 = base64.b64encode(test_data).decode("utf-8")

        await integration_test_client.post(
            "/s3/objects/upload",
            json={
                "bucket_name": test_bucket,
                "object_key": "metadata-test.txt",
                "data": data_base64,
                "content_type": "text/plain",
            },
        )

        response = await integration_test_client.post(
            "/s3/objects/metadata",
            json={
                "bucket_name": test_bucket,
                "object_key": "metadata-test.txt",
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["key"] == "metadata-test.txt"
        assert result["size"] == len(test_data)
        assert result["content_type"] == "text/plain"


# ============================================================================
# Тесты клиента S3Client напрямую (без API)
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
class TestClientPing:
    """Интеграционные тесты для ping через клиент."""

    async def test_ping(self, client: S3Client) -> None:
        """Тест ping с реальным S3."""
        result = await client.ping()
        assert result is True


@pytest.mark.integration
@pytest.mark.asyncio
class TestClientBucketOperations:
    """Интеграционные тесты для операций с bucket'ами через клиент."""

    async def test_bucket_exists(
        self,
        client: S3Client,
        test_bucket: str,
    ) -> None:
        """Тест проверки существования bucket'а."""
        exists = await client.bucket_exists(test_bucket)
        assert exists is True

        exists = await client.bucket_exists("non-existent-bucket")
        assert exists is False


@pytest.mark.integration
@pytest.mark.asyncio
class TestClientObjectOperations:
    """Интеграционные тесты для операций с объектами через клиент."""

    async def test_upload_and_download(
        self,
        client: S3Client,
        test_bucket: str,
    ) -> None:
        """Тест загрузки и скачивания объекта."""
        test_data = b"test upload download content"

        # Загружаем объект
        await client.upload_object(
            bucket_name=test_bucket,
            object_key="test-file.txt",
            data=test_data,
            content_type="text/plain",
        )

        # Проверяем существование
        exists = await client.object_exists(test_bucket, "test-file.txt")
        assert exists is True

        # Скачиваем объект
        downloaded_data = await client.download_object(
            bucket_name=test_bucket,
            object_key="test-file.txt",
        )
        assert downloaded_data == test_data

    async def test_list_objects(
        self,
        client: S3Client,
        test_bucket: str,
    ) -> None:
        """Тест получения списка объектов."""
        # Загружаем несколько объектов
        for i in range(3):
            await client.upload_object(
                bucket_name=test_bucket,
                object_key=f"test-{i}.txt",
                data=f"content {i}".encode(),
            )

        # Проверяем префикс - должны быть только наши объекты
        objects_with_prefix = await client.list_objects(test_bucket, prefix="test-")
        assert len(objects_with_prefix) >= 3
        # Проверяем, что все созданные объекты присутствуют
        object_keys = [obj["key"] for obj in objects_with_prefix]
        for i in range(3):
            assert f"test-{i}.txt" in object_keys

    async def test_delete_object(
        self,
        client: S3Client,
        test_bucket: str,
    ) -> None:
        """Тест удаления объекта."""
        # Загружаем объект
        await client.upload_object(
            bucket_name=test_bucket,
            object_key="delete-me.txt",
            data=b"delete this",
        )

        # Удаляем объект
        await client.delete_object(test_bucket, "delete-me.txt")

        # Проверяем, что объект удалён
        exists = await client.object_exists(test_bucket, "delete-me.txt")
        assert exists is False

    async def test_get_metadata(
        self,
        client: S3Client,
        test_bucket: str,
    ) -> None:
        """Тест получения метаданных объекта."""
        test_data = b"metadata test"
        await client.upload_object(
            bucket_name=test_bucket,
            object_key="metadata.txt",
            data=test_data,
            content_type="text/plain",
            metadata={"custom": "value"},
        )

        metadata = await client.get_object_metadata(test_bucket, "metadata.txt")
        assert metadata["key"] == "metadata.txt"
        assert metadata["size"] == len(test_data)
        assert metadata["content_type"] == "text/plain"
        assert metadata["metadata"]["custom"] == "value"

    async def test_copy_object(
        self,
        client: S3Client,
        test_bucket: str,
    ) -> None:
        """Тест копирования объекта."""
        test_data = b"copy test content"
        await client.upload_object(
            bucket_name=test_bucket,
            object_key="source.txt",
            data=test_data,
        )

        # Копируем объект
        await client.copy_object(
            source_bucket=test_bucket,
            source_key="source.txt",
            dest_bucket=test_bucket,
            dest_key="dest.txt",
        )

        # Проверяем, что оба объекта существуют
        assert await client.object_exists(test_bucket, "source.txt")
        assert await client.object_exists(test_bucket, "dest.txt")

        # Проверяем содержимое
        copied_data = await client.download_object(test_bucket, "dest.txt")
        assert copied_data == test_data


# ============================================================================
# Тесты для новых методов S3Client
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
class TestGetStream:
    """Тесты для метода get_stream()."""

    async def test_get_stream_success(
        self,
        client: S3Client,
        test_bucket: str,
    ) -> None:
        """Тест успешного получения потока для чтения."""
        # Загружаем тестовый объект
        test_data = b"test stream content" * 100  # Делаем побольше для теста
        await client.upload_object(
            bucket_name=test_bucket,
            object_key="stream-test.txt",
            data=test_data,
        )

        # Получаем поток
        stream = await client.get_stream(test_bucket, "stream-test.txt")

        # Читаем данные по частям
        chunks = []
        while True:
            chunk = await stream.read(1024)
            if not chunk:
                break
            chunks.append(chunk)

        # Проверяем, что данные совпадают
        read_data = b"".join(chunks)
        assert read_data == test_data

    async def test_get_stream_not_found(
        self,
        client: S3Client,
        test_bucket: str,
    ) -> None:
        """Тест получения потока для несуществующего объекта."""
        with pytest.raises(Exception):
            await client.get_stream(test_bucket, "non-existent.txt")


@pytest.mark.integration
@pytest.mark.asyncio
class TestDownloadObjectToFile:
    """Тесты для метода download_object_to_file()."""

    async def test_download_to_file_success(
        self,
        client: S3Client,
        test_bucket: str,
    ) -> None:
        """Тест успешного скачивания объекта в файл."""
        # Загружаем тестовый объект
        test_data = b"test file content for download"
        await client.upload_object(
            bucket_name=test_bucket,
            object_key="download-file-test.txt",
            data=test_data,
        )

        # Скачиваем в временный файл
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "downloaded.txt")

            result = await client.download_object_to_file(
                bucket_name=test_bucket,
                object_key="download-file-test.txt",
                file_path=file_path,
            )

            # Проверяем результат
            assert result["bucket_name"] == test_bucket
            assert result["object_key"] == "download-file-test.txt"
            assert result["file_path"] == file_path

            # Проверяем содержимое файла
            with open(file_path, "rb") as f:
                file_data = f.read()
            assert file_data == test_data

    async def test_download_to_file_with_subdir(
        self,
        client: S3Client,
        test_bucket: str,
    ) -> None:
        """Тест скачивания в файл с созданием поддиректории."""
        test_data = b"test content"
        await client.upload_object(
            bucket_name=test_bucket,
            object_key="subdir-test.txt",
            data=test_data,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "subdir", "file.txt")

            await client.download_object_to_file(
                bucket_name=test_bucket,
                object_key="subdir-test.txt",
                file_path=file_path,
            )

            # Проверяем, что файл создан
            assert os.path.exists(file_path)
            with open(file_path, "rb") as f:
                assert f.read() == test_data


@pytest.mark.integration
@pytest.mark.asyncio
class TestUploadObjectFromFile:
    """Тесты для метода upload_object_from_file()."""

    async def test_upload_from_file_success(
        self,
        client: S3Client,
        test_bucket: str,
    ) -> None:
        """Тест успешной загрузки файла с локальной файловой системы."""
        # Создаём временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmpfile:
            test_data = b"test upload from file content"
            tmpfile.write(test_data)
            tmpfile_path = tmpfile.name

        try:
            # Загружаем файл в S3
            result = await client.upload_object_from_file(
                bucket_name=test_bucket,
                object_key="upload-from-file-test.txt",
                file_path=tmpfile_path,
                content_type="text/plain",
            )

            # Проверяем результат
            assert result["bucket_name"] == test_bucket
            assert result["object_key"] == "upload-from-file-test.txt"

            # Проверяем, что файл загружен
            exists = await client.object_exists(
                test_bucket, "upload-from-file-test.txt"
            )
            assert exists is True

            # Проверяем содержимое
            downloaded_data = await client.download_object(
                test_bucket, "upload-from-file-test.txt"
            )
            assert downloaded_data == test_data
        finally:
            # Удаляем временный файл
            os.unlink(tmpfile_path)

    async def test_upload_from_file_with_metadata(
        self,
        client: S3Client,
        test_bucket: str,
    ) -> None:
        """Тест загрузки файла с метаданными."""
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            tmpfile.write(b"test with metadata")
            tmpfile_path = tmpfile.name

        try:
            await client.upload_object_from_file(
                bucket_name=test_bucket,
                object_key="metadata-file.txt",
                file_path=tmpfile_path,
                metadata={"custom": "value", "test": "data"},
            )

            # Проверяем метаданные
            metadata = await client.get_object_metadata(
                test_bucket, "metadata-file.txt"
            )
            assert metadata["metadata"]["custom"] == "value"
            assert metadata["metadata"]["test"] == "data"
        finally:
            os.unlink(tmpfile_path)


@pytest.mark.integration
@pytest.mark.asyncio
class TestUploadObjectWithFiles:
    """Тесты для upload_object() с поддержкой файлов."""

    async def test_upload_object_with_file_path(
        self,
        client: S3Client,
        test_bucket: str,
    ) -> None:
        """Тест загрузки объекта, передав путь к файлу."""
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            test_data = b"test upload with file path"
            tmpfile.write(test_data)
            tmpfile_path = tmpfile.name

        try:
            # Передаём путь к файлу вместо bytes
            result = await client.upload_object(
                bucket_name=test_bucket,
                object_key="file-path-test.txt",
                data=tmpfile_path,  # Передаём путь как строку
            )

            assert result["bucket_name"] == test_bucket
            assert result["object_key"] == "file-path-test.txt"

            # Проверяем содержимое
            downloaded_data = await client.download_object(
                test_bucket, "file-path-test.txt"
            )
            assert downloaded_data == test_data
        finally:
            os.unlink(tmpfile_path)

    async def test_upload_object_with_file_handle(
        self,
        client: S3Client,
        test_bucket: str,
    ) -> None:
        """Тест загрузки объекта, передав файловый дескриптор."""
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            test_data = b"test upload with file handle"
            tmpfile.write(test_data)
            tmpfile_path = tmpfile.name

        try:
            # Открываем файл и передаём дескриптор
            with open(tmpfile_path, "rb") as f:
                result = await client.upload_object(
                    bucket_name=test_bucket,
                    object_key="file-handle-test.txt",
                    data=f,  # Передаём файловый дескриптор
                )

            assert result["bucket_name"] == test_bucket

            # Проверяем содержимое
            downloaded_data = await client.download_object(
                test_bucket, "file-handle-test.txt"
            )
            assert downloaded_data == test_data
        finally:
            os.unlink(tmpfile_path)


@pytest.mark.integration
@pytest.mark.asyncio
class TestKeyMethod:
    """Тесты для метода key()."""

    async def test_key_without_s3_root(
        self,
        client: S3Client,
    ) -> None:
        """Тест key() без s3_root."""
        # Клиент создан без s3_root
        result = client.key("path", "to", "file.txt")
        assert result == "path/to/file.txt"

        result = client.key("/path/", "/to/", "/file.txt")
        assert result == "path/to/file.txt"

    async def test_key_with_s3_root(
        self,
        s3_session,
        test_bucket: str,
    ) -> None:
        """Тест key() с s3_root."""
        # Создаём клиент с s3_root
        client = S3Client(
            session=s3_session,
            endpoint_url=os.getenv("AWS_ENDPOINT_URL") or "http://localhost:9000",
            use_ssl=False,
            verify=False,
            s3_root="my-prefix",
        )

        result = client.key("path", "file.txt")
        assert result == "my-prefix/path/file.txt"

        result = client.key("/path/", "/file.txt")
        assert result == "my-prefix/path/file.txt"

    async def test_key_integration(
        self,
        s3_session,
        test_bucket: str,
    ) -> None:
        """Интеграционный тест key() с реальной загрузкой."""
        client = S3Client(
            session=s3_session,
            endpoint_url=os.getenv("AWS_ENDPOINT_URL") or "http://localhost:9000",
            use_ssl=False,
            verify=False,
            s3_root="test-prefix",
        )

        # Используем key() для создания пути
        object_key = client.key("test", "file.txt")
        assert object_key == "test-prefix/test/file.txt"

        # Загружаем объект с этим ключом
        await client.upload_object(
            bucket_name=test_bucket,
            object_key=object_key,
            data=b"test content",
        )

        # Проверяем, что объект существует по полному пути
        exists = await client.object_exists(test_bucket, object_key)
        assert exists is True

        # Проверяем, что объект не существует без префикса
        exists_without_prefix = await client.object_exists(
            test_bucket, "test/file.txt"
        )
        assert exists_without_prefix is False


@pytest.mark.integration
@pytest.mark.asyncio
class TestSyncDir:
    """Тесты для функции sync_dir()."""

    async def test_sync_dir_success(
        self,
        client: S3Client,
        test_bucket: str,
    ) -> None:
        """Тест успешной синхронизации директории."""
        # Загружаем несколько объектов с префиксом
        test_files = {
            "sync-test/file1.txt": b"content 1",
            "sync-test/file2.txt": b"content 2",
            "sync-test/subdir/file3.txt": b"content 3",
        }

        for key, content in test_files.items():
            await client.upload_object(
                bucket_name=test_bucket,
                object_key=key,
                data=content,
            )

        # Синхронизируем в временную директорию
        with tempfile.TemporaryDirectory() as tmpdir:
            await sync_dir(
                client=client,
                bucket_name=test_bucket,
                s3_prefix="sync-test",
                local_path=tmpdir,
            )

            # Проверяем, что все файлы скачаны
            assert os.path.exists(os.path.join(tmpdir, "file1.txt"))
            assert os.path.exists(os.path.join(tmpdir, "file2.txt"))
            assert os.path.exists(os.path.join(tmpdir, "subdir", "file3.txt"))

            # Проверяем содержимое
            with open(os.path.join(tmpdir, "file1.txt"), "rb") as f:
                assert f.read() == test_files["sync-test/file1.txt"]

            with open(os.path.join(tmpdir, "subdir", "file3.txt"), "rb") as f:
                assert f.read() == test_files["sync-test/subdir/file3.txt"]

    async def test_sync_dir_empty_prefix(
        self,
        client: S3Client,
        test_bucket: str,
    ) -> None:
        """Тест синхронизации без префикса (все объекты)."""
        # Загружаем объекты
        await client.upload_object(
            bucket_name=test_bucket,
            object_key="root-file.txt",
            data=b"root content",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            await sync_dir(
                client=client,
                bucket_name=test_bucket,
                s3_prefix="",  # Без префикса
                local_path=tmpdir,
            )

            # Проверяем, что файл скачан (может быть много файлов от других тестов)
            # Просто проверяем, что директория не пустая
            files = list(Path(tmpdir).rglob("*"))
            assert len(files) > 0

