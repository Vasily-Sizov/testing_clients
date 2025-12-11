"""
Интеграционные тесты с реальным S3.

Требуют запущенный S3 (например, MinIO через docker-compose).
Эти тесты проверяют:
1. Работу клиента S3Client напрямую
2. Работу API роутов через HTTP
"""
import base64
import pytest
from httpx import AsyncClient

from s3.client import S3Client


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
                "prefix": "",
                "max_keys": 100,
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["bucket_name"] == test_bucket
        assert len(result["objects"]) == 3


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

        objects = await client.list_objects(test_bucket)
        assert len(objects) == 3

        # Проверяем префикс
        objects_with_prefix = await client.list_objects(test_bucket, prefix="test-")
        assert len(objects_with_prefix) == 3

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

