"""
Интеграционные тесты с реальным Redis.

Требуют запущенный Redis (например, через docker-compose).
Эти тесты проверяют:
1. Работу клиента RedisClient напрямую
2. Работу API роутов через HTTP
"""
import pytest
from httpx import AsyncClient
from redis.asyncio import Redis

from my_redis_client.client.client import RedisClient


# ============================================================================
# Тесты API роутов
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
class TestPing:
    """Тесты для эндпоинта /ping."""

    async def test_ping_success(self, integration_test_client: AsyncClient) -> None:
        """Тест успешного ping с реальным Redis."""
        response = await integration_test_client.get("/redis/ping")

        assert response.status_code == 200
        assert response.json() == {"available": True}


@pytest.mark.integration
@pytest.mark.asyncio
class TestInfo:
    """Тесты для эндпоинта /info."""

    async def test_info_success(self, integration_test_client: AsyncClient) -> None:
        """Тест получения информации о Redis сервере."""
        response = await integration_test_client.get("/redis/info")

        assert response.status_code == 200
        info = response.json()
        assert "redis_version" in info or "server" in info


@pytest.mark.integration
@pytest.mark.asyncio
class TestListQueues:
    """Тесты для эндпоинта /queues."""

    async def test_list_queues_default(
        self,
        integration_test_client: AsyncClient,
        test_queue: str,
    ) -> None:
        """Тест списка очередей с дефолтным паттерном."""
        # Добавляем элемент в очередь, чтобы она появилась
        await integration_test_client.post(
            "/redis/queues/push",
            json={
                "queue_name": test_queue,
                "message": "test",
            },
        )

        response = await integration_test_client.get("/redis/queues")

        assert response.status_code == 200
        queues = response.json()
        assert isinstance(queues, list)
        assert test_queue in queues


# ============================================================================
# Тесты для работы с очередями через API
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
class TestQueuePush:
    """Тесты для эндпоинта /queues/push."""

    async def test_push_success(
        self,
        integration_test_client: AsyncClient,
        test_queue: str,
    ) -> None:
        """Тест успешного добавления сообщения в очередь."""
        response = await integration_test_client.post(
            "/redis/queues/push",
            json={
                "queue_name": test_queue,
                "message": "test message",
                "side": "left",
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["queue_name"] == test_queue
        assert result["size"] == 1

    async def test_push_dict_message(
        self,
        integration_test_client: AsyncClient,
        test_queue: str,
    ) -> None:
        """Тест добавления словаря в очередь."""
        response = await integration_test_client.post(
            "/redis/queues/push",
            json={
                "queue_name": test_queue,
                "message": {"task": "process", "id": 123},
                "side": "right",
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["size"] == 1


@pytest.mark.integration
@pytest.mark.asyncio
class TestQueuePop:
    """Тесты для эндпоинта /queues/pop."""

    async def test_pop_success(
        self,
        integration_test_client: AsyncClient,
        test_queue: str,
    ) -> None:
        """Тест успешного извлечения сообщения из очереди."""
        # Сначала добавляем сообщение
        await integration_test_client.post(
            "/redis/queues/push",
            json={
                "queue_name": test_queue,
                "message": "test pop",
            },
        )

        response = await integration_test_client.post(
            "/redis/queues/pop",
            json={
                "queue_name": test_queue,
                "side": "right",
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["queue_name"] == test_queue
        assert result["message"] == "test pop"

    async def test_pop_empty_queue(
        self,
        integration_test_client: AsyncClient,
        test_queue: str,
    ) -> None:
        """Тест извлечения из пустой очереди."""
        response = await integration_test_client.post(
            "/redis/queues/pop",
            json={
                "queue_name": test_queue,
            },
        )

        assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
class TestQueueBlockingPop:
    """Тесты для эндпоинта /queues/blocking-pop."""

    async def test_blocking_pop_success(
        self,
        integration_test_client: AsyncClient,
        test_queue: str,
    ) -> None:
        """Тест успешного блокирующего извлечения."""
        # Добавляем сообщение в отдельной задаче
        import asyncio
        async def add_message():
            await asyncio.sleep(0.1)
            await integration_test_client.post(
                "/redis/queues/push",
                json={
                    "queue_name": test_queue,
                    "message": "blocking test",
                },
            )

        # Запускаем добавление сообщения
        task = asyncio.create_task(add_message())

        # Пытаемся извлечь с таймаутом
        response = await integration_test_client.post(
            "/redis/queues/blocking-pop",
            json={
                "queue_names": test_queue,
                "timeout": 5,
            },
        )

        await task

        assert response.status_code == 200
        result = response.json()
        assert result["queue_name"] == test_queue
        assert result["message"] == "blocking test"


@pytest.mark.integration
@pytest.mark.asyncio
class TestQueueSize:
    """Тесты для эндпоинта /queues/size."""

    async def test_size_success(
        self,
        integration_test_client: AsyncClient,
        test_queue: str,
    ) -> None:
        """Тест получения размера очереди."""
        # Добавляем несколько сообщений
        for i in range(3):
            await integration_test_client.post(
                "/redis/queues/push",
                json={
                    "queue_name": test_queue,
                    "message": f"message {i}",
                },
            )

        response = await integration_test_client.post(
            "/redis/queues/size",
            json={
                "queue_name": test_queue,
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["queue_name"] == test_queue
        assert result["size"] == 3


@pytest.mark.integration
@pytest.mark.asyncio
class TestQueuePeek:
    """Тесты для эндпоинта /queues/peek."""

    async def test_peek_success(
        self,
        integration_test_client: AsyncClient,
        test_queue: str,
    ) -> None:
        """Тест просмотра элементов очереди."""
        # Добавляем сообщения
        for i in range(3):
            await integration_test_client.post(
                "/redis/queues/push",
                json={
                    "queue_name": test_queue,
                    "message": f"message {i}",
                },
            )

        response = await integration_test_client.post(
            "/redis/queues/peek",
            json={
                "queue_name": test_queue,
                "count": 2,
                "side": "left",
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["queue_name"] == test_queue
        assert len(result["messages"]) == 2
        # Проверяем, что очередь не изменилась
        size_response = await integration_test_client.post(
            "/redis/queues/size",
            json={"queue_name": test_queue},
        )
        assert size_response.json()["size"] == 3


@pytest.mark.integration
@pytest.mark.asyncio
class TestQueueClear:
    """Тесты для эндпоинта /queues/clear."""

    async def test_clear_success(
        self,
        integration_test_client: AsyncClient,
        test_queue: str,
    ) -> None:
        """Тест очистки очереди."""
        # Добавляем сообщения
        await integration_test_client.post(
            "/redis/queues/push",
            json={
                "queue_name": test_queue,
                "message": "test",
            },
        )

        response = await integration_test_client.post(
            "/redis/queues/clear",
            json={
                "queue_name": test_queue,
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["queue_name"] == test_queue

        # Проверяем, что очередь пуста
        size_response = await integration_test_client.post(
            "/redis/queues/size",
            json={"queue_name": test_queue},
        )
        assert size_response.json()["size"] == 0


@pytest.mark.integration
@pytest.mark.asyncio
class TestQueueExists:
    """Тесты для эндпоинта /queues/exists."""

    async def test_exists_true(
        self,
        integration_test_client: AsyncClient,
        test_queue: str,
    ) -> None:
        """Тест существующей очереди."""
        await integration_test_client.post(
            "/redis/queues/push",
            json={
                "queue_name": test_queue,
                "message": "test",
            },
        )

        response = await integration_test_client.post(
            "/redis/queues/exists",
            json={
                "queue_name": test_queue,
            },
        )

        assert response.status_code == 200
        assert response.json()["exists"] is True

    async def test_exists_false(
        self,
        integration_test_client: AsyncClient,
    ) -> None:
        """Тест несуществующей очереди."""
        response = await integration_test_client.post(
            "/redis/queues/exists",
            json={
                "queue_name": "non-existent-queue",
            },
        )

        assert response.status_code == 200
        assert response.json()["exists"] is False


# ============================================================================
# Тесты клиента RedisClient напрямую (без API)
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
class TestClientPing:
    """Интеграционные тесты для ping через клиент."""

    async def test_ping(self, client: RedisClient) -> None:
        """Тест ping с реальным Redis."""
        result = await client.ping()
        assert result is True


@pytest.mark.integration
@pytest.mark.asyncio
class TestClientInfo:
    """Интеграционные тесты для info через клиент."""

    async def test_info(self, client: RedisClient) -> None:
        """Тест получения информации о Redis сервере."""
        info = await client.info()
        assert "redis_version" in info or "server" in info


@pytest.mark.integration
@pytest.mark.asyncio
class TestClientQueueOperations:
    """Интеграционные тесты для операций с очередями через клиент."""

    async def test_push_and_pop(
        self,
        client: RedisClient,
        test_queue: str,
    ) -> None:
        """Тест добавления и извлечения сообщения."""
        # Добавляем сообщение
        size = await client.queue_push(test_queue, "test message", side="left")
        assert size == 1

        # Извлекаем сообщение
        message = await client.queue_pop(test_queue, side="right")
        assert message == "test message"

        # Очередь должна быть пуста
        size_after = await client.queue_size(test_queue)
        assert size_after == 0

    async def test_push_dict(
        self,
        client: RedisClient,
        test_queue: str,
    ) -> None:
        """Тест добавления словаря в очередь."""
        message_dict = {"task": "process", "id": 123}
        await client.queue_push(test_queue, message_dict)

        message = await client.queue_pop(test_queue)
        import json
        assert json.loads(message) == message_dict

    async def test_blocking_pop(
        self,
        client: RedisClient,
        test_queue: str,
    ) -> None:
        """Тест блокирующего извлечения."""
        import asyncio

        # Добавляем сообщение в отдельной задаче
        async def add_message():
            await asyncio.sleep(0.1)
            await client.queue_push(test_queue, "blocking message")

        task = asyncio.create_task(add_message())

        # Пытаемся извлечь с таймаутом
        result = await client.queue_blocking_pop(test_queue, timeout=5)
        await task

        assert result is not None
        queue_name, message = result
        assert queue_name == test_queue
        assert message == "blocking message"

    async def test_queue_size(
        self,
        client: RedisClient,
        test_queue: str,
    ) -> None:
        """Тест получения размера очереди."""
        # Добавляем несколько сообщений
        for i in range(5):
            await client.queue_push(test_queue, f"message {i}")

        size = await client.queue_size(test_queue)
        assert size == 5

    async def test_queue_peek(
        self,
        client: RedisClient,
        test_queue: str,
    ) -> None:
        """Тест просмотра элементов очереди."""
        # Добавляем сообщения
        for i in range(3):
            await client.queue_push(test_queue, f"message {i}")

        # Просматриваем элементы
        messages = await client.queue_peek(test_queue, count=2, side="left")
        assert len(messages) == 2

        # Проверяем, что очередь не изменилась
        size = await client.queue_size(test_queue)
        assert size == 3

    async def test_queue_clear(
        self,
        client: RedisClient,
        test_queue: str,
    ) -> None:
        """Тест очистки очереди."""
        # Добавляем сообщения
        await client.queue_push(test_queue, "test")

        # Очищаем
        cleared = await client.queue_clear(test_queue)
        assert cleared is True

        # Проверяем, что очередь пуста
        size = await client.queue_size(test_queue)
        assert size == 0

    async def test_queue_exists(
        self,
        client: RedisClient,
        test_queue: str,
    ) -> None:
        """Тест проверки существования очереди."""
        # Очередь не существует
        exists = await client.queue_exists(test_queue)
        assert exists is False

        # Добавляем сообщение
        await client.queue_push(test_queue, "test")

        # Очередь существует
        exists = await client.queue_exists(test_queue)
        assert exists is True

