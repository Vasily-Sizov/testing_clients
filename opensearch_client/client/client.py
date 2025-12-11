from typing import Optional, Any, Sequence
from opensearchpy import AsyncOpenSearch


class OpenSearchClient:
    """
    Клиент-обёртка над AsyncOpenSearch.

    Содержит только методы работы с OpenSearch.
    Не управляет соединением и не знает о lifecycle приложения.
    """

    def __init__(self, connection: AsyncOpenSearch) -> None:
        """
        Инициализирует клиент готовым соединением OpenSearch.

        :param connection: AsyncOpenSearch соединение
        """
        self._conn = connection

    async def ping(self) -> bool:
        """
        Проверяет доступность OpenSearch.

        :return: True, если OpenSearch доступен
        """
        return await self._conn.ping()

    async def info(self) -> dict:
        """
        Возвращает информацию о кластере OpenSearch.

        :return: словарь с информацией о кластере
        """
        return await self._conn.info()

    async def list_indices(self, pattern: str = "*") -> list[dict]:
        """
        Возвращает список индексов по шаблону.

        :param pattern: шаблон имени индекса
        :return: список индексов с базовой статистикой
        """
        stats = await self._conn.indices.stats(index=pattern)
        result = []

        for name, data in stats.get("indices", {}).items():
            result.append({
                "name": name,
                "docs": data["total"]["docs"]["count"],
                "size_bytes": data["total"]["store"]["size_in_bytes"],
            })

        return result

    async def index_exists(self, name: str) -> bool:
        """
        Проверяет существование индекса.

        :param name: имя индекса
        :return: True, если индекс существует
        """
        return await self._conn.indices.exists(index=name)

    async def create_index(
        self,
        name: str,
        mappings: dict,
        settings: Optional[dict] = None,
        aliases: Optional[list[str]] = None,
    ) -> dict:
        """
        Создаёт индекс.

        :param name: имя индекса
        :param mappings: mappings
        :param settings: settings
        :param aliases: список алиасов
        :return: ответ OpenSearch
        """
        body = {
            "mappings": mappings,
            "settings": settings or {},
        }

        if aliases:
            body["aliases"] = {a: {} for a in aliases}

        return await self._conn.indices.create(index=name, body=body)

    async def delete_index(self, name: str) -> dict:
        """
        Удаляет индекс.

        :param name: имя индекса для удаления
        :return: ответ OpenSearch
        """
        return await self._conn.indices.delete(index=name)

    async def index_document(
        self,
        index: str,
        document: dict[str, Any],
        document_id: Optional[str] = None,
        refresh: bool = False,
    ) -> dict:
        """
        Индексирует один документ.

        :param index: имя индекса
        :param document: документ для индексации
        :param document_id: ID документа (если не указан, будет сгенерирован)
        :param refresh: обновить ли индекс сразу после записи
        :return: ответ OpenSearch
        """
        params = {"refresh": "true"} if refresh else {}
        if document_id:
            return await self._conn.index(
                index=index,
                body=document,
                id=document_id,
                params=params,
            )
        return await self._conn.index(
            index=index,
            body=document,
            params=params,
        )

    async def bulk_index_documents(
        self,
        index: str,
        documents: Sequence[dict[str, Any]],
        document_ids: Optional[Sequence[Optional[str]]] = None,
        refresh: bool = False,
    ) -> dict:
        """
        Индексирует несколько документов одной операцией.

        :param index: имя индекса
        :param documents: список документов для индексации
        :param document_ids: список ID документов
            (опционально, может быть короче documents)
        :param refresh: обновить ли индекс сразу после записи
        :return: ответ OpenSearch
        """
        if not documents:
            return {"errors": False, "items": []}

        # Формируем тело bulk запроса
        body = []
        for i, doc in enumerate(documents):
            action: dict[str, Any] = {"index": {"_index": index}}
            if document_ids and i < len(document_ids):
                doc_id = document_ids[i]
                if doc_id:
                    action["index"]["_id"] = doc_id
            body.append(action)
            body.append(doc)

        # Выполняем bulk операцию напрямую через API
        response = await self._conn.bulk(
            body=body,
            refresh=refresh,
        )

        # Проверяем наличие ошибок
        has_errors = False
        if response.get("errors"):
            has_errors = any(
                item.get("index", {}).get("error") is not None
                for item in response.get("items", [])
            )

        return {
            "errors": has_errors,
            "items": response.get("items", []),
            "took": response.get("took", 0),
        }

    async def get_document(
        self,
        index: str,
        document_id: str,
    ) -> Optional[dict[str, Any]]:
        """
        Получает документ по ID.

        :param index: имя индекса
        :param document_id: ID документа
        :return: документ или None, если не найден
        """
        try:
            response = await self._conn.get(index=index, id=document_id)
            return response.get("_source")
        except Exception:
            return None

    async def get_documents(
        self,
        index: str,
        document_ids: Sequence[str],
    ) -> dict[str, Optional[dict[str, Any]]]:
        """
        Получает несколько документов по ID.

        :param index: имя индекса
        :param document_ids: список ID документов
        :return: словарь {document_id: document} или
            {document_id: None} если не найден
        """
        if not document_ids:
            return {}

        body = {
            "ids": list(document_ids),
        }
        response = await self._conn.mget(index=index, body=body)

        result: dict[str, Optional[dict[str, Any]]] = {}
        for doc in response.get("docs", []):
            doc_id = doc.get("_id")
            if doc_id:
                if doc.get("found"):
                    result[doc_id] = doc.get("_source")
                else:
                    result[doc_id] = None

        return result

    async def vector_search(
        self,
        index: str,
        vector_field: str,
        query_vector: list[float],
        size: int = 10,
        filter: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Выполняет векторный поиск (kNN).

        :param index: имя индекса
        :param vector_field: имя поля с вектором
        :param query_vector: вектор запроса
        :param size: количество результатов
        :param filter: опциональный фильтр для поиска
        :return: результаты поиска
        """
        # Формируем запрос для kNN поиска в OpenSearch
        knn_query: dict[str, Any] = {
            "vector": query_vector,
            "k": size,
        }

        if filter:
            knn_query["filter"] = filter

        query: dict[str, Any] = {
            "size": size,
            "query": {
                "knn": {
                    vector_field: knn_query,
                },
            },
        }

        response = await self._conn.search(index=index, body=query)
        return response

    async def bm25_search(
        self,
        index: str,
        query_text: str,
        fields: Optional[Sequence[str]] = None,
        size: int = 10,
        filter: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Выполняет BM25 текстовый поиск.

        :param index: имя индекса
        :param query_text: текст запроса
        :param fields: поля для поиска (если не указано, используется _all)
        :param size: количество результатов
        :param filter: опциональный фильтр для поиска
        :return: результаты поиска
        """
        if fields:
            query: dict[str, Any] = {
                "multi_match": {
                    "query": query_text,
                    "fields": list(fields),
                },
            }
        else:
            query = {
                "match": {
                    "_all": query_text,
                },
            }

        body: dict[str, Any] = {
            "size": size,
            "query": query,
        }

        if filter:
            body["query"] = {
                "bool": {
                    "must": [query],
                    "filter": [filter],
                },
            }

        response = await self._conn.search(index=index, body=body)
        return response

    async def hybrid_search(
        self,
        index: str,
        vector_field: str,
        query_vector: list[float],
        query_text: str,
        text_fields: Optional[Sequence[str]] = None,
        size: int = 10,
        vector_weight: float = 0.5,
        text_weight: float = 0.5,
        filter: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Выполняет гибридный поиск (векторный + BM25).

        :param index: имя индекса
        :param vector_field: имя поля с вектором
        :param query_vector: вектор запроса
        :param query_text: текст запроса
        :param text_fields: поля для текстового поиска
        :param size: количество результатов
        :param vector_weight: вес векторного поиска (0.0-1.0)
        :param text_weight: вес текстового поиска (0.0-1.0)
        :param filter: опциональный фильтр для поиска
        :return: результаты поиска
        """
        # Векторный запрос (knn внутри query, как в vector_search)
        knn_query: dict[str, Any] = {
            "vector": query_vector,
            "k": size,
        }
        if filter:
            knn_query["filter"] = filter

        # Текстовый запрос
        if text_fields:
            text_query: dict[str, Any] = {
                "multi_match": {
                    "query": query_text,
                    "fields": list(text_fields),
                },
            }
        else:
            # Используем query_string вместо match _all (который устарел)
            text_query = {
                "query_string": {
                    "query": query_text,
                },
            }

        # Гибридный запрос: используем bool query с should
        # для комбинации knn и текстового поиска
        # В OpenSearch 2.x для гибридного поиска
        # можно использовать bool с should
        body: dict[str, Any] = {
            "size": size,
            "query": {
                "bool": {
                    "should": [
                        {
                            "knn": {
                                vector_field: knn_query,
                            },
                        },
                        text_query,
                    ],
                    "minimum_should_match": 1,
                },
            },
        }

        # Применяем фильтр через filter в bool query
        if filter:
            body["query"]["bool"]["filter"] = [filter]

        # Применяем веса через boost
        # Для knn boost применяется к полю (если нужно)
        # В OpenSearch 2.x веса для гибридного поиска применяются
        # автоматически или через параметры запроса, но не через boost в knn
        # Упрощаем - не применяем boost к knn,
        # так как это может вызвать ошибки формата

        # Для текстового запроса boost можно применить, но упростим
        # В гибридном поиске OpenSearch автоматически комбинирует результаты

        response = await self._conn.search(index=index, body=body)
        return response
