import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI

from my_opensearch_client.endpoint.routes import opensearch_router
from my_opensearch_client.client.client import OpenSearchClient
from my_opensearch_client.client.connection import create_opensearch_connection
from my_opensearch_client.endpoint.base_settings import get_opensearch_settings

# Настройка логирования
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Имя тестового индекса
TEST_INDEX_NAME = "test_connection_index"


@asynccontextmanager
async def test_opensearch_connection_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan для проверки подключения к OpenSearch в test_app.
    
    Создаёт соединение, выполняет проверки (ping, info, список индексов,
    создание индекса, индексация документов, поиск и т.д.),
    выводит результаты в логи, затем закрывает соединение.
    Не влияет на основной lifespan роутера.
    """
    logger.info("=" * 60)
    logger.info("Начинаем проверку подключения к OpenSearch...")
    logger.info("=" * 60)
    
    settings = get_opensearch_settings()
    
    # Создаём соединение
    connection = create_opensearch_connection(
        hosts=settings.hosts_list,
        username=settings.opensearch_username,
        password=settings.opensearch_password,
        timeout=settings.opensearch_timeout,
        max_retries=settings.opensearch_max_retries,
        retry_on_timeout=settings.opensearch_retry_on_timeout,
        verify_certs=settings.opensearch_verify_certs,
    )
    
    # Создаём клиент
    client = OpenSearchClient(connection)
    
    test_index_created = False
    
    try:
        # Проверка 1: Ping
        logger.info("\n[1/9] Проверка ping...")
        try:
            ping_result = await client.ping()
            logger.info(f"✓ Ping результат: {ping_result}")
        except Exception as e:
            logger.error(f"✗ Ошибка ping: {e}")
        
        # Проверка 2: Информация о кластере
        logger.info("\n[2/9] Получение информации о кластере...")
        try:
            cluster_info = await client.info()
            logger.info(f"✓ Информация о кластере:")
            logger.info(f"  - Название: {cluster_info.get('name', 'N/A')}")
            logger.info(f"  - Версия: {cluster_info.get('version', {}).get('number', 'N/A')}")
            logger.info(f"  - UUID кластера: {cluster_info.get('cluster_uuid', 'N/A')}")
        except Exception as e:
            logger.error(f"✗ Ошибка получения информации о кластере: {e}")
        
        # Проверка 3: Список индексов
        logger.info("\n[3/9] Получение списка индексов...")
        try:
            indices = await client.list_indices()
            logger.info(f"✓ Найдено индексов: {len(indices)}")
            if indices:
                logger.info("  Список индексов (первые 10):")
                for idx in indices[:10]:
                    logger.info(f"    - {idx['name']} (документов: {idx['docs']}, размер: {idx['size_bytes']} байт)")
                if len(indices) > 10:
                    logger.info(f"    ... и ещё {len(indices) - 10} индексов")
            else:
                logger.info("  Индексы не найдены")
        except Exception as e:
            logger.error(f"✗ Ошибка получения списка индексов: {e}")
        
        # Проверка 4: Проверка существования тестового индекса
        logger.info(f"\n[4/9] Проверка существования индекса '{TEST_INDEX_NAME}'...")
        try:
            index_exists = await client.index_exists(TEST_INDEX_NAME)
            logger.info(f"✓ Индекс '{TEST_INDEX_NAME}' существует: {index_exists}")
            if index_exists:
                logger.info(f"  (индекс уже существует, будет использован для тестов)")
        except Exception as e:
            logger.error(f"✗ Ошибка проверки существования индекса: {e}")
        
        # Проверка 5: Создание тестового индекса
        logger.info(f"\n[5/9] Создание тестового индекса '{TEST_INDEX_NAME}'...")
        try:
            # Сначала удаляем, если существует
            if await client.index_exists(TEST_INDEX_NAME):
                await client.delete_index(TEST_INDEX_NAME)
                logger.info(f"  Удалён существующий индекс '{TEST_INDEX_NAME}'")
            
            # Создаём новый индекс
            mappings = {
                "properties": {
                    "title": {"type": "text"},
                    "content": {"type": "text"},
                    "category": {"type": "keyword"},
                    "rating": {"type": "float"},
                }
            }
            index_settings = {
                "number_of_shards": 1,
                "number_of_replicas": 0,
            }
            create_result = await client.create_index(
                name=TEST_INDEX_NAME,
                mappings=mappings,
                settings=index_settings,
            )
            test_index_created = True
            logger.info(f"✓ Индекс '{TEST_INDEX_NAME}' успешно создан")
            logger.info(f"  Результат: {create_result.get('acknowledged', False)}")
        except Exception as e:
            logger.error(f"✗ Ошибка создания индекса: {e}")
        
        # Проверка 6: Индексация одного документа
        logger.info(f"\n[6/9] Индексация одного документа в '{TEST_INDEX_NAME}'...")
        try:
            test_doc = {
                "title": "Тестовый документ",
                "content": "Это тестовый документ для проверки работы OpenSearch клиента",
                "category": "test",
                "rating": 4.5,
            }
            index_result = await client.index_document(
                index=TEST_INDEX_NAME,
                document=test_doc,
                document_id="test_doc_1",
                refresh=True,
            )
            logger.info(f"✓ Документ успешно проиндексирован")
            logger.info(f"  ID: {index_result.get('_id', 'N/A')}")
            logger.info(f"  Индекс: {index_result.get('_index', 'N/A')}")
        except Exception as e:
            logger.error(f"✗ Ошибка индексации документа: {e}")
        
        # Проверка 7: Массовая индексация документов
        logger.info(f"\n[7/9] Массовая индексация документов в '{TEST_INDEX_NAME}'...")
        try:
            bulk_docs = [
                {
                    "title": f"Документ {i}",
                    "content": f"Содержимое документа номер {i} для тестирования",
                    "category": "test",
                    "rating": 3.0 + (i * 0.3),
                }
                for i in range(2, 6)  # Создаём документы с ID 2-5
            ]
            bulk_result = await client.bulk_index_documents(
                index=TEST_INDEX_NAME,
                documents=bulk_docs,
                document_ids=[f"test_doc_{i}" for i in range(2, 6)],
                refresh=True,
            )
            logger.info(f"✓ Массовая индексация завершена")
            logger.info(f"  Обработано документов: {len(bulk_result.get('items', []))}")
            logger.info(f"  Есть ошибки: {bulk_result.get('errors', True)}")
            if bulk_result.get('errors'):
                logger.warning(f"  ⚠ Внимание: при массовой индексации были ошибки")
        except Exception as e:
            logger.error(f"✗ Ошибка массовой индексации: {e}")
        
        # Проверка 8: Получение документа по ID
        logger.info(f"\n[8/9] Получение документа по ID из '{TEST_INDEX_NAME}'...")
        try:
            document = await client.get_document(
                index=TEST_INDEX_NAME,
                document_id="test_doc_1",
            )
            if document:
                logger.info(f"✓ Документ успешно получен")
                logger.info(f"  Содержимое: {document}")
            else:
                logger.warning(f"  ⚠ Документ не найден")
        except Exception as e:
            logger.error(f"✗ Ошибка получения документа: {e}")
        
        # Проверка 9: Текстовый поиск (BM25)
        logger.info(f"\n[9/9] Выполнение текстового поиска (BM25) в '{TEST_INDEX_NAME}'...")
        try:
            search_result = await client.bm25_search(
                index=TEST_INDEX_NAME,
                query_text="тестовый",
                fields=["title", "content"],
                size=5,
            )
            hits = search_result.get("hits", {}).get("hits", [])
            total = search_result.get("hits", {}).get("total", {})
            logger.info(f"✓ Поиск выполнен успешно")
            logger.info(f"  Найдено документов: {total.get('value', 0) if isinstance(total, dict) else total}")
            logger.info(f"  Возвращено результатов: {len(hits)}")
            if hits:
                logger.info("  Первые результаты:")
                for hit in hits[:3]:
                    logger.info(f"    - ID: {hit.get('_id')}, Score: {hit.get('_score', 0):.4f}")
        except Exception as e:
            logger.error(f"✗ Ошибка выполнения поиска: {e}")
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ Проверка подключения к OpenSearch завершена!")
        logger.info("=" * 60 + "\n")
        
    except Exception as e:
        logger.error("\n" + "=" * 60)
        logger.error(f"✗ Критическая ошибка при проверке подключения: {e}")
        logger.error("=" * 60 + "\n", exc_info=True)
    
    finally:
        # Очистка: удаляем тестовый индекс, если был создан
        if test_index_created:
            logger.info(f"\nОчистка: удаление тестового индекса '{TEST_INDEX_NAME}'...")
            try:
                await client.delete_index(TEST_INDEX_NAME)
                logger.info(f"✓ Тестовый индекс '{TEST_INDEX_NAME}' удалён")
            except Exception as e:
                logger.warning(f"⚠ Не удалось удалить тестовый индекс: {e}")
        
        # Закрываем соединение
        await connection.close()
        logger.info("Соединение с OpenSearch закрыто")
    
    yield


app = FastAPI(
    title="OpenSearch Test App",
    description="Тестовое приложение для проверки работы OpenSearch клиента",
    version="1.0.0",
    lifespan=test_opensearch_connection_lifespan,
)

app.include_router(opensearch_router)
