"""
Модели данных для API запросов OpenSearch.

Содержит Pydantic модели для валидации входящих запросов.
"""
from typing import Any, Optional
from pydantic import BaseModel, Field


class IndexDocumentRequest(BaseModel):
    """
    Запрос на индексацию одного документа.

    :param index: имя индекса, в который будет добавлен документ
    :param document: документ для индексации (словарь с данными)
    :param document_id: опциональный ID документа (если не указан, будет сгенерирован)
    :param refresh: обновить ли индекс сразу после записи (по умолчанию False)
    """

    index: str = Field(..., description="Имя индекса")
    document: dict[str, Any] = Field(..., description="Документ для индексации")
    document_id: Optional[str] = Field(None, description="ID документа")
    refresh: bool = Field(False, description="Обновить индекс сразу")


class BulkIndexRequest(BaseModel):
    """
    Запрос на массовую индексацию документов.

    :param index: имя индекса, в который будут добавлены документы
    :param documents: список документов для индексации
    :param document_ids: опциональный список ID документов (может быть короче documents)
    :param refresh: обновить ли индекс сразу после записи (по умолчанию False)
    """

    index: str = Field(..., description="Имя индекса")
    documents: list[dict[str, Any]] = Field(..., description="Список документов")
    document_ids: Optional[list[Optional[str]]] = Field(
        None,
        description="Список ID документов",
    )
    refresh: bool = Field(False, description="Обновить индекс сразу")


class GetDocumentRequest(BaseModel):
    """
    Запрос на получение документа по ID.

    :param index: имя индекса
    :param document_id: ID документа для получения
    """

    index: str = Field(..., description="Имя индекса")
    document_id: str = Field(..., description="ID документа")


class GetDocumentsRequest(BaseModel):
    """
    Запрос на получение нескольких документов по ID.

    :param index: имя индекса
    :param document_ids: список ID документов для получения
    """

    index: str = Field(..., description="Имя индекса")
    document_ids: list[str] = Field(..., description="Список ID документов")


class VectorSearchRequest(BaseModel):
    """
    Запрос на векторный поиск (kNN).

    :param index: имя индекса для поиска
    :param vector_field: имя поля с вектором в индексе
    :param query_vector: вектор запроса для поиска похожих документов
    :param size: количество результатов для возврата (от 1 до 1000)
    :param filter: опциональный фильтр для ограничения поиска
    """

    index: str = Field(..., description="Имя индекса")
    vector_field: str = Field(..., description="Имя поля с вектором")
    query_vector: list[float] = Field(..., description="Вектор запроса")
    size: int = Field(10, ge=1, le=1000, description="Количество результатов")
    filter: Optional[dict[str, Any]] = Field(None, description="Фильтр для поиска")


class BM25SearchRequest(BaseModel):
    """
    Запрос на BM25 текстовый поиск.

    :param index: имя индекса для поиска
    :param query_text: текст запроса для поиска
    :param fields: опциональный список полей для поиска (если не указан, используется _all)
    :param size: количество результатов для возврата (от 1 до 1000)
    :param filter: опциональный фильтр для ограничения поиска
    """

    index: str = Field(..., description="Имя индекса")
    query_text: str = Field(..., description="Текст запроса")
    fields: Optional[list[str]] = Field(None, description="Поля для поиска")
    size: int = Field(10, ge=1, le=1000, description="Количество результатов")
    filter: Optional[dict[str, Any]] = Field(None, description="Фильтр для поиска")


class HybridSearchRequest(BaseModel):
    """
    Запрос на гибридный поиск (векторный + BM25).

    Комбинирует результаты векторного и текстового поиска с заданными весами.

    :param index: имя индекса для поиска
    :param vector_field: имя поля с вектором в индексе
    :param query_vector: вектор запроса для векторного поиска
    :param query_text: текст запроса для текстового поиска
    :param text_fields: опциональный список полей для текстового поиска
    :param size: количество результатов для возврата (от 1 до 1000)
    :param vector_weight: вес векторного поиска (от 0.0 до 1.0, по умолчанию 0.5)
    :param text_weight: вес текстового поиска (от 0.0 до 1.0, по умолчанию 0.5)
    :param filter: опциональный фильтр для ограничения поиска
    """

    index: str = Field(..., description="Имя индекса")
    vector_field: str = Field(..., description="Имя поля с вектором")
    query_vector: list[float] = Field(..., description="Вектор запроса")
    query_text: str = Field(..., description="Текст запроса")
    text_fields: Optional[list[str]] = Field(
        None,
        description="Поля для текстового поиска",
    )
    size: int = Field(10, ge=1, le=1000, description="Количество результатов")
    vector_weight: float = Field(0.5, ge=0.0, le=1.0, description="Вес векторного поиска")
    text_weight: float = Field(0.5, ge=0.0, le=1.0, description="Вес текстового поиска")
    filter: Optional[dict[str, Any]] = Field(None, description="Фильтр для поиска")

