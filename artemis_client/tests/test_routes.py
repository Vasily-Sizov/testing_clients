"""
Интеграционные тесты с реальным Artemis.

Требуют запущенный Artemis (например, через docker-compose).
Эти тесты проверяют:
1. Работу клиента ArtemisClient напрямую
2. Работу API роутов через HTTP
"""
import pytest
from httpx import AsyncClient

from my_artemis_client.client.client import ArtemisClient


# ============================================================================
# Тесты API роутов
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
class TestSendMessage:
    """Тесты для эндпоинта /send."""

    async def test_send_message_success(
        self,
        integration_test_client: AsyncClient,
        test_queue: str,
    ) -> None:
        """Тест успешной отправки сообщения."""
        response = await integration_test_client.post(
            "/artemis/send",
            json={
                "queue": test_queue,
                "body": "test message",
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["queue"] == test_queue
        assert result["body"] == "test message"
        assert "Message sent successfully" in result["message"]


@pytest.mark.integration
@pytest.mark.asyncio
class TestSendMessageValidation:
    """Тесты валидации запросов."""

    async def test_send_message_missing_queue(
        self,
        integration_test_client: AsyncClient,
    ) -> None:
        """Тест отправки без указания очереди."""
        response = await integration_test_client.post(
            "/artemis/send",
            json={
                "body": "test message",
            },
        )

        assert response.status_code == 422  # Validation error

    async def test_send_message_missing_body(
        self,
        integration_test_client: AsyncClient,
        test_queue: str,
    ) -> None:
        """Тест отправки без указания тела сообщения."""
        response = await integration_test_client.post(
            "/artemis/send",
            json={
                "queue": test_queue,
            },
        )

        assert response.status_code == 422  # Validation error


# ============================================================================
# Тесты клиента ArtemisClient напрямую (без API)
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
class TestClientSendMessage:
    """Интеграционные тесты для send_message через клиент."""

    async def test_send_message(self, client: ArtemisClient, test_queue: str) -> None:
        """Тест отправки сообщения через клиент."""
        result = await client.send_message(test_queue, "test message from client")
        assert result is True

    async def test_send_message_multiple(
        self,
        client: ArtemisClient,
        test_queue: str,
    ) -> None:
        """Тест отправки нескольких сообщений."""
        messages = ["message 1", "message 2", "message 3"]
        for msg in messages:
            result = await client.send_message(test_queue, msg)
            assert result is True

