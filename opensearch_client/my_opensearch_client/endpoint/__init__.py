"""
Модуль endpoint для OpenSearch клиента.

Содержит FastAPI роуты, lifespan управление, модели данных и настройки.
"""
from my_opensearch_client.endpoint.routes import opensearch_router
from my_opensearch_client.endpoint.lifespan import opensearch_lifespan
from my_opensearch_client.endpoint.entities import (
    IndexDocumentRequest,
    BulkIndexRequest,
    GetDocumentRequest,
    GetDocumentsRequest,
    VectorSearchRequest,
    BM25SearchRequest,
    HybridSearchRequest,
)
from my_opensearch_client.endpoint.base_settings import OpenSearchSettings, get_opensearch_settings

__all__ = [
    "opensearch_router",
    "opensearch_lifespan",
    "IndexDocumentRequest",
    "BulkIndexRequest",
    "GetDocumentRequest",
    "GetDocumentsRequest",
    "VectorSearchRequest",
    "BM25SearchRequest",
    "HybridSearchRequest",
    "OpenSearchSettings",
    "get_opensearch_settings",
]

