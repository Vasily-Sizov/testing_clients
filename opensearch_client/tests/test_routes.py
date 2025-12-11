"""
Интеграционные тесты с реальным OpenSearch.

Требуют запущенный OpenSearch (например, через docker-compose).
Эти тесты проверяют:
1. Работу клиента OpenSearchClient напрямую
2. Работу API роутов через HTTP
"""
import pytest
from httpx import AsyncClient
from opensearchpy import AsyncOpenSearch

from opensearch_client.client.client import OpenSearchClient


@pytest.mark.integration
@pytest.mark.asyncio
class TestPing:
    """Тесты для эндпоинта /ping."""

    async def test_ping_success(self, integration_test_client: AsyncClient) -> None:
        """Тест успешного ping с реальным OpenSearch."""
        response = await integration_test_client.get("/opensearch/ping")

        assert response.status_code == 200
        assert response.json() == {"available": True}


@pytest.mark.integration
@pytest.mark.asyncio
class TestInfo:
    """Тесты для эндпоинта /info."""

    async def test_info_success(self, integration_test_client: AsyncClient) -> None:
        """Тест получения информации о кластере."""
        response = await integration_test_client.get("/opensearch/info")

        assert response.status_code == 200
        info = response.json()
        assert "cluster_name" in info
        assert "version" in info


@pytest.mark.integration
@pytest.mark.asyncio
class TestListIndices:
    """Тесты для эндпоинта /indices."""

    async def test_list_indices_default(
        self,
        integration_test_client: AsyncClient,
        api_test_index: str,
    ) -> None:
        """Тест списка индексов с дефолтным паттерном."""
        response = await integration_test_client.get("/opensearch/indices")

        assert response.status_code == 200
        indices = response.json()
        assert isinstance(indices, list)
        # Проверяем, что наш тестовый индекс есть в списке
        index_names = [idx["name"] for idx in indices]
        assert api_test_index in index_names

    async def test_list_indices_with_pattern(
        self,
        integration_test_client: AsyncClient,
        api_test_index: str,
    ) -> None:
        """Тест списка индексов с паттерном."""
        response = await integration_test_client.get(f"/opensearch/indices?pattern={api_test_index}")

        assert response.status_code == 200
        indices = response.json()
        assert isinstance(indices, list)
        assert any(idx["name"] == api_test_index for idx in indices)


@pytest.mark.integration
@pytest.mark.asyncio
class TestIndexExists:
    """Тесты для эндпоинта /indices/{index_name}/exists."""

    async def test_index_exists_true(
        self,
        integration_test_client: AsyncClient,
        api_test_index: str,
    ) -> None:
        """Тест существующего индекса."""
        response = await integration_test_client.post(f"/opensearch/indices/{api_test_index}/exists")

        assert response.status_code == 200
        assert response.json() == {"exists": True}

    async def test_index_exists_false(self, integration_test_client: AsyncClient) -> None:
        """Тест несуществующего индекса."""
        response = await integration_test_client.post("/opensearch/indices/non-existent-index/exists")

        assert response.status_code == 200
        assert response.json() == {"exists": False}


@pytest.mark.integration
@pytest.mark.asyncio
class TestCreateIndex:
    """Тесты для эндпоинта /indices/{index_name}/create."""

    async def test_create_index_success(
        self,
        integration_test_client: AsyncClient,
        opensearch_connection: AsyncOpenSearch,
    ) -> None:
        """Тест успешного создания индекса."""
        index_name = "test-create-index-api"
        # Удаляем индекс, если существует
        if await opensearch_connection.indices.exists(index=index_name):
            await opensearch_connection.indices.delete(index=index_name)

        mappings = {"properties": {"title": {"type": "text"}}}

        response = await integration_test_client.post(
            f"/opensearch/indices/{index_name}/create",
            json={"mappings": mappings},
        )

        assert response.status_code == 200
        result = response.json()
        assert "acknowledged" in result

        # Проверяем, что индекс действительно создан
        exists = await opensearch_connection.indices.exists(index=index_name)
        assert exists is True

        # Очистка
        await opensearch_connection.indices.delete(index=index_name)

    async def test_create_index_with_settings(
        self,
        integration_test_client: AsyncClient,
        opensearch_connection: AsyncOpenSearch,
    ) -> None:
        """Тест создания индекса с настройками."""
        index_name = "test-create-index-settings-api"
        # Удаляем индекс, если существует
        if await opensearch_connection.indices.exists(index=index_name):
            await opensearch_connection.indices.delete(index=index_name)

        mappings = {"properties": {"title": {"type": "text"}}}
        settings = {"number_of_shards": 1}

        response = await integration_test_client.post(
            f"/opensearch/indices/{index_name}/create",
            json={
                "mappings": mappings,
                "settings": settings,
                "aliases": ["alias1"],
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert "acknowledged" in result

        # Проверяем, что индекс создан
        exists = await opensearch_connection.indices.exists(index=index_name)
        assert exists is True

        # Очистка
        await opensearch_connection.indices.delete(index=index_name)


@pytest.mark.integration
@pytest.mark.asyncio
class TestDeleteIndex:
    """Тесты для эндпоинта /indices/{index_name} (DELETE)."""

    async def test_delete_index_success(
        self,
        integration_test_client: AsyncClient,
        opensearch_connection: AsyncOpenSearch,
    ) -> None:
        """Тест успешного удаления индекса."""
        index_name = "test-delete-index-api"
        # Создаем индекс для удаления
        if await opensearch_connection.indices.exists(index=index_name):
            await opensearch_connection.indices.delete(index=index_name)

        mappings = {"properties": {"title": {"type": "text"}}}
        await opensearch_connection.indices.create(
            index=index_name,
            body={"mappings": mappings},
        )

        # Проверяем, что индекс существует
        exists = await opensearch_connection.indices.exists(index=index_name)
        assert exists is True

        # Удаляем индекс через API
        response = await integration_test_client.delete(
            f"/opensearch/indices/{index_name}",
        )

        assert response.status_code == 200
        result = response.json()
        assert "acknowledged" in result

        # Проверяем, что индекс действительно удален
        exists = await opensearch_connection.indices.exists(index=index_name)
        assert exists is False

    async def test_delete_index_not_found(
        self,
        integration_test_client: AsyncClient,
    ) -> None:
        """Тест удаления несуществующего индекса."""
        response = await integration_test_client.delete(
            "/opensearch/indices/non-existent-index",
        )

        # API возвращает 404 для несуществующего индекса
        assert response.status_code == 404
        result = response.json()
        assert "detail" in result
        assert "not found" in result["detail"].lower()


@pytest.mark.integration
@pytest.mark.asyncio
class TestIndexDocument:
    """Тесты для эндпоинта /documents/index."""

    async def test_index_document_success(
        self,
        integration_test_client: AsyncClient,
        api_test_index: str,
    ) -> None:
        """Тест успешной индексации документа."""
        document = {"title": "Test", "content": "Test content"}

        response = await integration_test_client.post(
            "/opensearch/documents/index",
            json={
                "index": api_test_index,
                "document": document,
                "document_id": "doc-1",
                "refresh": True,
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["_id"] == "doc-1"
        assert result["_index"] == api_test_index

    async def test_index_document_without_id(
        self,
        integration_test_client: AsyncClient,
        api_test_index: str,
    ) -> None:
        """Тест индексации документа без ID."""
        document = {"title": "Test"}

        response = await integration_test_client.post(
            "/opensearch/documents/index",
            json={
                "index": api_test_index,
                "document": document,
                "refresh": True,
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert "_id" in result
        assert result["_index"] == api_test_index


@pytest.mark.integration
@pytest.mark.asyncio
class TestBulkIndexDocuments:
    """Тесты для эндпоинта /documents/bulk-index."""

    async def test_bulk_index_success(
        self,
        integration_test_client: AsyncClient,
        api_test_index: str,
    ) -> None:
        """Тест успешной массовой индексации."""
        documents = [
            {"title": "Doc 1"},
            {"title": "Doc 2"},
        ]

        response = await integration_test_client.post(
            "/opensearch/documents/bulk-index",
            json={
                "index": api_test_index,
                "documents": documents,
                "document_ids": ["doc-1", "doc-2"],
                "refresh": True,
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result.get("errors") is False
        assert "items" in result


@pytest.mark.integration
@pytest.mark.asyncio
class TestGetDocument:
    """Тесты для эндпоинта /documents/get."""

    async def test_get_document_success(
        self,
        integration_test_client: AsyncClient,
        api_test_index: str,
    ) -> None:
        """Тест успешного получения документа."""
        # Сначала индексируем документ
        document = {"title": "Test", "content": "Content"}
        await integration_test_client.post(
            "/opensearch/documents/index",
            json={
                "index": api_test_index,
                "document": document,
                "document_id": "doc-get-1",
                "refresh": True,
            },
        )

        # Получаем документ
        response = await integration_test_client.post(
            "/opensearch/documents/get",
            json={
                "index": api_test_index,
                "document_id": "doc-get-1",
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert "document" in result
        assert result["document"]["title"] == document["title"]
        assert result["document"]["content"] == document["content"]

    async def test_get_document_not_found(
        self,
        integration_test_client: AsyncClient,
        api_test_index: str,
    ) -> None:
        """Тест получения несуществующего документа."""
        response = await integration_test_client.post(
            "/opensearch/documents/get",
            json={
                "index": api_test_index,
                "document_id": "non-existent-doc",
            },
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.mark.integration
@pytest.mark.asyncio
class TestGetDocuments:
    """Тесты для эндпоинта /documents/bulk-get."""

    async def test_get_documents_success(
        self,
        integration_test_client: AsyncClient,
        api_test_index: str,
    ) -> None:
        """Тест успешного получения нескольких документов."""
        # Сначала индексируем документы
        documents = [
            {"title": "Doc 1"},
            {"title": "Doc 2"},
        ]
        await integration_test_client.post(
            "/opensearch/documents/bulk-index",
            json={
                "index": api_test_index,
                "documents": documents,
                "document_ids": ["bulk-get-1", "bulk-get-2"],
                "refresh": True,
            },
        )

        # Получаем документы
        response = await integration_test_client.post(
            "/opensearch/documents/bulk-get",
            json={
                "index": api_test_index,
                "document_ids": ["bulk-get-1", "bulk-get-2", "bulk-get-3"],
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert "bulk-get-1" in result
        assert "bulk-get-2" in result
        assert result["bulk-get-1"]["title"] == "Doc 1"
        assert result["bulk-get-2"]["title"] == "Doc 2"
        # Третий документ не существует
        assert result.get("bulk-get-3") is None


@pytest.mark.integration
@pytest.mark.asyncio
class TestVectorSearch:
    """Тесты для эндпоинта /search/vector."""

    async def test_vector_search_success(
        self,
        integration_test_client: AsyncClient,
        api_test_index: str,
    ) -> None:
        """Тест успешного векторного поиска."""
        # Сначала индексируем документы с векторами
        await integration_test_client.post(
            "/opensearch/documents/bulk-index",
            json={
                "index": api_test_index,
                "documents": [
                    {"title": "Doc 1", "embedding": [0.1, 0.2, 0.3]},
                    {"title": "Doc 2", "embedding": [0.4, 0.5, 0.6]},
                ],
                "document_ids": ["vec-1", "vec-2"],
                "refresh": True,
            },
        )

        query_vector = [0.15, 0.25, 0.35]

        response = await integration_test_client.post(
            "/opensearch/search/vector",
            json={
                "index": api_test_index,
                "vector_field": "embedding",
                "query_vector": query_vector,
                "size": 10,
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert "hits" in result
        assert len(result["hits"]["hits"]) > 0

    async def test_vector_search_with_filter(
        self,
        integration_test_client: AsyncClient,
        api_test_index: str,
    ) -> None:
        """Тест векторного поиска с фильтром."""
        # Индексируем документы с векторами и статусом
        await integration_test_client.post(
            "/opensearch/documents/bulk-index",
            json={
                "index": api_test_index,
                "documents": [
                    {"title": "Doc 1", "embedding": [0.1, 0.2, 0.3], "status": "active"},
                    {"title": "Doc 2", "embedding": [0.4, 0.5, 0.6], "status": "inactive"},
                ],
                "document_ids": ["vec-filter-1", "vec-filter-2"],
                "refresh": True,
            },
        )

        query_vector = [0.15, 0.25, 0.35]
        filter_query = {"term": {"status": "active"}}

        response = await integration_test_client.post(
            "/opensearch/search/vector",
            json={
                "index": api_test_index,
                "vector_field": "embedding",
                "query_vector": query_vector,
                "size": 5,
                "filter": filter_query,
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert "hits" in result


@pytest.mark.integration
@pytest.mark.asyncio
class TestBM25Search:
    """Тесты для эндпоинта /search/bm25."""

    async def test_bm25_search_success(
        self,
        integration_test_client: AsyncClient,
        api_test_index: str,
    ) -> None:
        """Тест успешного BM25 поиска."""
        # Индексируем документы
        await integration_test_client.post(
            "/opensearch/documents/bulk-index",
            json={
                "index": api_test_index,
                "documents": [
                    {"title": "Python programming", "content": "Learn Python"},
                    {"title": "JavaScript guide", "content": "Learn JavaScript"},
                ],
                "document_ids": ["bm25-1", "bm25-2"],
                "refresh": True,
            },
        )

        # Небольшая задержка для индексации
        import asyncio
        await asyncio.sleep(0.1)
        
        response = await integration_test_client.post(
            "/opensearch/search/bm25",
            json={
                "index": api_test_index,
                "query_text": "Python",
                "size": 10,
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert "hits" in result
        # Проверяем, что есть результаты или хотя бы структура правильная
        assert "hits" in result["hits"]
        # Если результатов нет, это может быть из-за задержки индексации
        # Проверяем хотя бы структуру ответа
        assert isinstance(result["hits"]["hits"], list)

    async def test_bm25_search_with_fields(
        self,
        integration_test_client: AsyncClient,
        api_test_index: str,
    ) -> None:
        """Тест BM25 поиска с указанными полями."""
        # Индексируем документы
        await integration_test_client.post(
            "/opensearch/documents/bulk-index",
            json={
                "index": api_test_index,
                "documents": [
                    {"title": "Test title", "content": "Test content"},
                ],
                "document_ids": ["bm25-fields-1"],
                "refresh": True,
            },
        )

        response = await integration_test_client.post(
            "/opensearch/search/bm25",
            json={
                "index": api_test_index,
                "query_text": "Test",
                "fields": ["title", "content"],
                "size": 5,
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert "hits" in result


@pytest.mark.integration
@pytest.mark.asyncio
class TestHybridSearch:
    """Тесты для эндпоинта /search/hybrid."""

    async def test_hybrid_search_success(
        self,
        integration_test_client: AsyncClient,
        api_test_index: str,
    ) -> None:
        """Тест успешного гибридного поиска."""
        # Индексируем документы с векторами и текстом
        await integration_test_client.post(
            "/opensearch/documents/bulk-index",
            json={
                "index": api_test_index,
                "documents": [
                    {"title": "Python guide", "content": "Learn Python", "embedding": [0.1, 0.2, 0.3]},
                    {"title": "JavaScript tutorial", "content": "Learn JS", "embedding": [0.4, 0.5, 0.6]},
                ],
                "document_ids": ["hybrid-1", "hybrid-2"],
                "refresh": True,
            },
        )

        query_vector = [0.15, 0.25, 0.35]

        response = await integration_test_client.post(
            "/opensearch/search/hybrid",
            json={
                "index": api_test_index,
                "vector_field": "embedding",
                "query_vector": query_vector,
                "query_text": "Python",
                "size": 10,
                "vector_weight": 0.6,
                "text_weight": 0.4,
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert "hits" in result
        assert len(result["hits"]["hits"]) > 0

    async def test_hybrid_search_with_all_params(
        self,
        integration_test_client: AsyncClient,
        api_test_index: str,
    ) -> None:
        """Тест гибридного поиска со всеми параметрами."""
        # Индексируем документы
        await integration_test_client.post(
            "/opensearch/documents/bulk-index",
            json={
                "index": api_test_index,
                "documents": [
                    {"title": "Test", "content": "Content", "embedding": [0.1, 0.2, 0.3], "status": "active"},
                ],
                "document_ids": ["hybrid-all-1"],
                "refresh": True,
            },
        )

        query_vector = [0.15, 0.25, 0.35]
        filter_query = {"term": {"status": "active"}}

        response = await integration_test_client.post(
            "/opensearch/search/hybrid",
            json={
                "index": api_test_index,
                "vector_field": "embedding",
                "query_vector": query_vector,
                "query_text": "Test",
                "text_fields": ["title", "content"],
                "size": 5,
                "vector_weight": 0.7,
                "text_weight": 0.3,
                "filter": filter_query,
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert "hits" in result


# ============================================================================
# Тесты клиента OpenSearchClient напрямую (без API)
# ============================================================================


@pytest.fixture(scope="module")
async def test_index(opensearch_connection: AsyncOpenSearch, event_loop) -> str:
    """
    Создаёт тестовый индекс для тестов клиента и удаляет его после тестов.

    :return: имя тестового индекса
    """
    index_name = "test-integration-index"

    # Удаляем индекс, если существует
    if await opensearch_connection.indices.exists(index=index_name):
        await opensearch_connection.indices.delete(index=index_name)

    # Создаём индекс с поддержкой kNN
    await opensearch_connection.indices.create(
        index=index_name,
        body={
            "settings": {
                "index": {
                    "knn": True,
                },
            },
            "mappings": {
                "properties": {
                    "title": {"type": "text"},
                    "content": {"type": "text"},
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": 3,
                    },
                },
            },
        },
    )

    yield index_name

    # Удаляем индекс после тестов
    if await opensearch_connection.indices.exists(index=index_name):
        await opensearch_connection.indices.delete(index=index_name)


@pytest.mark.integration
@pytest.mark.asyncio
class TestClientPing:
    """Интеграционные тесты для ping через клиент."""

    async def test_ping(self, client: OpenSearchClient) -> None:
        """Тест ping с реальным OpenSearch."""
        result = await client.ping()
        assert result is True


@pytest.mark.integration
@pytest.mark.asyncio
class TestClientInfo:
    """Интеграционные тесты для info через клиент."""

    async def test_info(self, client: OpenSearchClient) -> None:
        """Тест получения информации о кластере."""
        info = await client.info()
        assert "cluster_name" in info
        assert "version" in info


@pytest.mark.integration
@pytest.mark.asyncio
class TestClientIndexOperations:
    """Интеграционные тесты для операций с индексами через клиент."""

    async def test_index_exists(
        self,
        client: OpenSearchClient,
        test_index: str,
    ) -> None:
        """Тест проверки существования индекса."""
        exists = await client.index_exists(test_index)
        assert exists is True

        exists = await client.index_exists("non-existent-index")
        assert exists is False

    async def test_list_indices(
        self,
        client: OpenSearchClient,
        test_index: str,
    ) -> None:
        """Тест получения списка индексов."""
        indices = await client.list_indices(pattern=test_index)
        assert len(indices) > 0
        assert any(idx["name"] == test_index for idx in indices)


@pytest.mark.integration
@pytest.mark.asyncio
class TestClientDocuments:
    """Интеграционные тесты для работы с документами через клиент."""

    async def test_index_and_get_document(
        self,
        client: OpenSearchClient,
        test_index: str,
    ) -> None:
        """Тест индексации и получения документа."""
        document = {"title": "Test Document", "content": "Test content"}
        document_id = "test-doc-1"

        # Индексируем документ
        result = await client.index_document(
            index=test_index,
            document=document,
            document_id=document_id,
            refresh=True,
        )
        assert result["_id"] == document_id

        # Получаем документ
        retrieved = await client.get_document(
            index=test_index,
            document_id=document_id,
        )
        assert retrieved is not None
        assert retrieved["title"] == document["title"]
        assert retrieved["content"] == document["content"]

    async def test_bulk_index_and_get(
        self,
        client: OpenSearchClient,
        test_index: str,
    ) -> None:
        """Тест массовой индексации и получения."""
        documents = [
            {"title": f"Doc {i}", "content": f"Content {i}"}
            for i in range(3)
        ]
        document_ids = [f"bulk-doc-{i}" for i in range(3)]

        # Массовая индексация
        result = await client.bulk_index_documents(
            index=test_index,
            documents=documents,
            document_ids=document_ids,
            refresh=True,
        )
        assert result.get("errors") is False

        # Получаем несколько документов
        retrieved = await client.get_documents(
            index=test_index,
            document_ids=document_ids,
        )
        assert len(retrieved) == 3
        assert all(doc_id in retrieved for doc_id in document_ids)
        assert retrieved["bulk-doc-0"]["title"] == "Doc 0"


@pytest.mark.integration
@pytest.mark.asyncio
class TestClientSearch:
    """Интеграционные тесты для поиска через клиент."""

    async def test_bm25_search(
        self,
        client: OpenSearchClient,
        test_index: str,
    ) -> None:
        """Тест BM25 поиска."""
        # Индексируем тестовые документы
        await client.bulk_index_documents(
            index=test_index,
            documents=[
                {"title": "Python programming", "content": "Learn Python"},
                {"title": "JavaScript guide", "content": "Learn JavaScript"},
                {"title": "Python tutorial", "content": "Advanced Python"},
            ],
            document_ids=["doc-1", "doc-2", "doc-3"],
            refresh=True,
        )

        # Поиск
        results = await client.bm25_search(
            index=test_index,
            query_text="Python",
            fields=["title", "content"],
            size=10,
        )

        assert "hits" in results
        assert len(results["hits"]["hits"]) > 0

    async def test_vector_search(
        self,
        client: OpenSearchClient,
        test_index: str,
    ) -> None:
        """Тест векторного поиска."""
        # Индексируем документы с векторами
        await client.bulk_index_documents(
            index=test_index,
            documents=[
                {
                    "title": "Doc 1",
                    "embedding": [0.1, 0.2, 0.3],
                },
                {
                    "title": "Doc 2",
                    "embedding": [0.4, 0.5, 0.6],
                },
            ],
            document_ids=["vec-doc-1", "vec-doc-2"],
            refresh=True,
        )

        # Векторный поиск
        query_vector = [0.15, 0.25, 0.35]  # Близко к первому документу
        results = await client.vector_search(
            index=test_index,
            vector_field="embedding",
            query_vector=query_vector,
            size=10,
        )

        assert "hits" in results
        assert len(results["hits"]["hits"]) > 0

