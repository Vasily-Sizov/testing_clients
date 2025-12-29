from typing import Any, Optional
from fastapi import APIRouter, Request, HTTPException, Depends
from opensearchpy.exceptions import NotFoundError

from my_opensearch_client.client.client import OpenSearchClient
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


opensearch_router = APIRouter(
    prefix="/opensearch", tags=["opensearch"], lifespan=opensearch_lifespan
)


def get_opensearch_client(request: Request) -> OpenSearchClient:
    """
    Dependency для получения OpenSearchClient из state приложения.

    :param request: FastAPI request
    :return: OpenSearchClient
    :raises HTTPException: если клиент не найден в state
    """
    client = getattr(request.app.state, "opensearch_client", None)
    if client is None:
        raise HTTPException(
            status_code=500,
            detail="OpenSearch client not initialized",
        )
    return client


# Эндпоинты
@opensearch_router.get("/ping")
async def ping(
    client: OpenSearchClient = Depends(get_opensearch_client),
) -> dict[str, bool]:
    """Проверяет доступность OpenSearch."""
    is_available = await client.ping()
    return {"available": is_available}


@opensearch_router.get("/info")
async def info(
    client: OpenSearchClient = Depends(get_opensearch_client),
) -> dict[str, Any]:
    """Возвращает информацию о кластере OpenSearch."""
    return await client.info()


@opensearch_router.get("/indices")
async def list_indices(
    pattern: str = "*",
    client: OpenSearchClient = Depends(get_opensearch_client),
) -> list[dict[str, Any]]:
    """Возвращает список индексов."""
    return await client.list_indices(pattern=pattern)


@opensearch_router.post("/indices/{index_name}/exists")
async def index_exists(
    index_name: str,
    client: OpenSearchClient = Depends(get_opensearch_client),
) -> dict[str, bool]:
    """Проверяет существование индекса."""
    exists = await client.index_exists(index_name)
    return {"exists": exists}


@opensearch_router.post("/indices/{index_name}/create")
async def create_index(
    index_name: str,
    mappings: dict[str, Any],
    settings: Optional[dict[str, Any]] = None,
    aliases: Optional[list[str]] = None,
    client: OpenSearchClient = Depends(get_opensearch_client),
) -> dict[str, Any]:
    """Создаёт индекс."""
    return await client.create_index(
        name=index_name,
        mappings=mappings,
        settings=settings,
        aliases=aliases,
    )


@opensearch_router.delete("/indices/{index_name}")
async def delete_index(
    index_name: str,
    client: OpenSearchClient = Depends(get_opensearch_client),
) -> dict[str, Any]:
    """Удаляет индекс по имени."""
    try:
        return await client.delete_index(name=index_name)
    except NotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Index not found: {index_name}",
        )


@opensearch_router.post("/documents/index")
async def index_document(
    request: IndexDocumentRequest,
    client: OpenSearchClient = Depends(get_opensearch_client),
) -> dict[str, Any]:
    """Индексирует один документ."""
    return await client.index_document(
        index=request.index,
        document=request.document,
        document_id=request.document_id,
        refresh=request.refresh,
    )


@opensearch_router.post("/documents/bulk-index")
async def bulk_index_documents(
    request: BulkIndexRequest,
    client: OpenSearchClient = Depends(get_opensearch_client),
) -> dict[str, Any]:
    """Индексирует несколько документов."""
    return await client.bulk_index_documents(
        index=request.index,
        documents=request.documents,
        document_ids=request.document_ids,
        refresh=request.refresh,
    )


@opensearch_router.post("/documents/get")
async def get_document(
    request: GetDocumentRequest,
    client: OpenSearchClient = Depends(get_opensearch_client),
) -> dict[str, Any]:
    """Получает документ по ID."""
    document = await client.get_document(
        index=request.index,
        document_id=request.document_id,
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"document": document}


@opensearch_router.post("/documents/bulk-get")
async def get_documents(
    request: GetDocumentsRequest,
    client: OpenSearchClient = Depends(get_opensearch_client),
) -> dict[str, Optional[dict[str, Any]]]:
    """Получает несколько документов по ID."""
    return await client.get_documents(
        index=request.index,
        document_ids=request.document_ids,
    )


@opensearch_router.post("/search/vector")
async def vector_search(
    request: VectorSearchRequest,
    client: OpenSearchClient = Depends(get_opensearch_client),
) -> dict[str, Any]:
    """Выполняет векторный поиск (kNN)."""
    return await client.vector_search(
        index=request.index,
        vector_field=request.vector_field,
        query_vector=request.query_vector,
        size=request.size,
        filter=request.filter,
    )


@opensearch_router.post("/search/bm25")
async def bm25_search(
    request: BM25SearchRequest,
    client: OpenSearchClient = Depends(get_opensearch_client),
) -> dict[str, Any]:
    """Выполняет BM25 текстовый поиск."""
    return await client.bm25_search(
        index=request.index,
        query_text=request.query_text,
        fields=request.fields,
        size=request.size,
        filter=request.filter,
    )


@opensearch_router.post("/search/hybrid")
async def hybrid_search(
    request: HybridSearchRequest,
    client: OpenSearchClient = Depends(get_opensearch_client),
) -> dict[str, Any]:
    """Выполняет гибридный поиск (векторный + BM25)."""
    return await client.hybrid_search(
        index=request.index,
        vector_field=request.vector_field,
        query_vector=request.query_vector,
        query_text=request.query_text,
        text_fields=request.text_fields,
        size=request.size,
        vector_weight=request.vector_weight,
        text_weight=request.text_weight,
        filter=request.filter,
    )
