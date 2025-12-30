import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI

from my_redis_client.endpoint.routes import redis_router
from my_redis_client.client.client import RedisClient
from my_redis_client.client.connection import create_redis_connection
from my_redis_client.endpoint.base_settings import get_settings

# Настройка логирования
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Имя тестовой очереди
TEST_QUEUE_NAME = "test_connection_queue"


@asynccontextmanager
async def test_redis_connection_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan для проверки подключения к Redis в test_app.
    
    Создаёт соединение, выполняет проверки (ping, info, список очередей,
    работа с очередями: push, pop, peek, blocking pop и т.д.),
    выводит результаты в логи, затем закрывает соединение.
    Не влияет на основной lifespan роутера.
    """
    logger.info("=" * 60)
    logger.info("Начинаем проверку подключения к Redis...")
    logger.info("=" * 60)
    
    settings = get_settings()
    
    # Создаём соединение
    connection = create_redis_connection(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        username=settings.redis_username,
        password=settings.redis_password,
        decode_responses=settings.redis_decode_responses,
        socket_timeout=settings.redis_socket_timeout,
        socket_connect_timeout=settings.redis_socket_connect_timeout,
        retry_on_timeout=settings.redis_retry_on_timeout,
        health_check_interval=settings.redis_health_check_interval,
    )
    
    # Создаём клиент
    client = RedisClient(connection)
    
    test_queue_cleared = False
    
    try:
        # Проверка 1: Ping
        logger.info("\n[1/11] Проверка ping...")
        try:
            ping_result = await client.ping()
            logger.info(f"✓ Ping результат: {ping_result}")
        except Exception as e:
            logger.error(f"✗ Ошибка ping: {e}")
        
        # Проверка 2: Информация о сервере
        logger.info("\n[2/11] Получение информации о Redis сервере...")
        try:
            server_info = await client.info("server")
            logger.info(f"✓ Информация о сервере:")
            logger.info(f"  - Версия Redis: {server_info.get('redis_version', 'N/A')}")
            logger.info(f"  - Режим: {server_info.get('redis_mode', 'N/A')}")
            logger.info(f"  - Операционная система: {server_info.get('os', 'N/A')}")
            
            memory_info = await client.info("memory")
            logger.info(f"✓ Информация о памяти:")
            logger.info(f"  - Использовано памяти: {memory_info.get('used_memory_human', 'N/A')}")
            logger.info(f"  - Пиковое использование: {memory_info.get('used_memory_peak_human', 'N/A')}")
        except Exception as e:
            logger.error(f"✗ Ошибка получения информации о сервере: {e}")
        
        # Проверка 3: Список всех очередей
        logger.info("\n[3/11] Получение списка всех очередей...")
        try:
            all_queues = await client.queue_list_all("*")
            logger.info(f"✓ Найдено очередей: {len(all_queues)}")
            if all_queues:
                logger.info("  Список очередей (первые 10):")
                for queue in all_queues[:10]:
                    size = await client.queue_size(queue)
                    logger.info(f"    - {queue} (размер: {size})")
                if len(all_queues) > 10:
                    logger.info(f"    ... и ещё {len(all_queues) - 10} очередей")
            else:
                logger.info("  Очереди не найдены")
        except Exception as e:
            logger.error(f"✗ Ошибка получения списка очередей: {e}")
        
        # Проверка 4: Проверка существования тестовой очереди
        logger.info(f"\n[4/11] Проверка существования очереди '{TEST_QUEUE_NAME}'...")
        try:
            queue_exists = await client.queue_exists(TEST_QUEUE_NAME)
            logger.info(f"✓ Очередь '{TEST_QUEUE_NAME}' существует: {queue_exists}")
            if queue_exists:
                size = await client.queue_size(TEST_QUEUE_NAME)
                logger.info(f"  Размер очереди: {size}")
        except Exception as e:
            logger.error(f"✗ Ошибка проверки существования очереди: {e}")
        
        # Проверка 5: Очистка тестовой очереди (если существует)
        logger.info(f"\n[5/11] Очистка тестовой очереди '{TEST_QUEUE_NAME}'...")
        try:
            cleared = await client.queue_clear(TEST_QUEUE_NAME)
            test_queue_cleared = True
            if cleared:
                logger.info(f"✓ Очередь '{TEST_QUEUE_NAME}' очищена")
            else:
                logger.info(f"✓ Очередь '{TEST_QUEUE_NAME}' была пуста или не существует")
        except Exception as e:
            logger.error(f"✗ Ошибка очистки очереди: {e}")
        
        # Проверка 6: Добавление одного сообщения в очередь
        logger.info(f"\n[6/11] Добавление одного сообщения в очередь '{TEST_QUEUE_NAME}'...")
        try:
            test_message = {"type": "test", "content": "Тестовое сообщение", "number": 1}
            size = await client.queue_push(
                queue_name=TEST_QUEUE_NAME,
                message=test_message,
                side="right",
            )
            logger.info(f"✓ Сообщение успешно добавлено")
            logger.info(f"  Размер очереди после добавления: {size}")
        except Exception as e:
            logger.error(f"✗ Ошибка добавления сообщения: {e}")
        
        # Проверка 7: Просмотр элементов очереди (peek)
        logger.info(f"\n[7/11] Просмотр элементов очереди '{TEST_QUEUE_NAME}' (peek)...")
        try:
            peeked = await client.queue_peek(
                queue_name=TEST_QUEUE_NAME,
                count=3,
                side="left",
            )
            logger.info(f"✓ Просмотр выполнен успешно")
            logger.info(f"  Просмотрено элементов: {len(peeked)}")
            for i, msg in enumerate(peeked, 1):
                logger.info(f"    {i}. {msg}")
        except Exception as e:
            logger.error(f"✗ Ошибка просмотра элементов: {e}")
        
        # Проверка 8: Размер очереди
        logger.info(f"\n[8/11] Проверка размера очереди '{TEST_QUEUE_NAME}'...")
        try:
            size = await client.queue_size(TEST_QUEUE_NAME)
            logger.info(f"✓ Размер очереди: {size}")
        except Exception as e:
            logger.error(f"✗ Ошибка получения размера очереди: {e}")
        
        # Проверка 9: Массовое добавление сообщений
        logger.info(f"\n[9/11] Массовое добавление сообщений в очередь '{TEST_QUEUE_NAME}'...")
        try:
            bulk_messages = [
                {"type": "test", "content": f"Сообщение номер {i}", "number": i}
                for i in range(2, 6)
            ]
            for msg in bulk_messages:
                await client.queue_push(
                    queue_name=TEST_QUEUE_NAME,
                    message=msg,
                    side="right",
                )
            final_size = await client.queue_size(TEST_QUEUE_NAME)
            logger.info(f"✓ Массовое добавление завершено")
            logger.info(f"  Добавлено сообщений: {len(bulk_messages)}")
            logger.info(f"  Итоговый размер очереди: {final_size}")
        except Exception as e:
            logger.error(f"✗ Ошибка массового добавления: {e}")
        
        # Проверка 10: Извлечение сообщения из очереди (pop)
        logger.info(f"\n[10/11] Извлечение сообщения из очереди '{TEST_QUEUE_NAME}' (pop)...")
        try:
            popped = await client.queue_pop(
                queue_name=TEST_QUEUE_NAME,
                side="left",
            )
            if popped:
                logger.info(f"✓ Сообщение успешно извлечено")
                logger.info(f"  Содержимое: {popped}")
                remaining_size = await client.queue_size(TEST_QUEUE_NAME)
                logger.info(f"  Осталось элементов в очереди: {remaining_size}")
            else:
                logger.warning(f"  ⚠ Очередь пуста")
        except Exception as e:
            logger.error(f"✗ Ошибка извлечения сообщения: {e}")
        
        # Проверка 11: Блокирующее извлечение сообщения (blocking pop)
        logger.info(f"\n[11/11] Блокирующее извлечение сообщения из очереди '{TEST_QUEUE_NAME}' (blocking pop)...")
        try:
            blocked_result = await client.queue_blocking_pop(
                queue_names=TEST_QUEUE_NAME,
                timeout=2,
                side="left",
            )
            if blocked_result:
                queue_name, message = blocked_result
                logger.info(f"✓ Сообщение успешно извлечено (блокирующий режим)")
                logger.info(f"  Очередь: {queue_name}")
                logger.info(f"  Содержимое: {message}")
            else:
                logger.warning(f"  ⚠ Таймаут: сообщение не получено в течение 2 секунд")
        except Exception as e:
            logger.error(f"✗ Ошибка блокирующего извлечения: {e}")
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ Проверка подключения к Redis завершена!")
        logger.info("=" * 60 + "\n")
        
    except Exception as e:
        logger.error("\n" + "=" * 60)
        logger.error(f"✗ Критическая ошибка при проверке подключения: {e}")
        logger.error("=" * 60 + "\n", exc_info=True)
    
    finally:
        # Очистка: удаляем тестовую очередь, если была очищена
        if test_queue_cleared:
            logger.info(f"\nОчистка: удаление тестовой очереди '{TEST_QUEUE_NAME}'...")
            try:
                await client.queue_clear(TEST_QUEUE_NAME)
                logger.info(f"✓ Тестовая очередь '{TEST_QUEUE_NAME}' очищена")
            except Exception as e:
                logger.warning(f"⚠ Не удалось очистить тестовую очередь: {e}")
        
        # Закрываем соединение
        await connection.aclose()
        logger.info("Соединение с Redis закрыто")
    
    yield


app = FastAPI(
    title="Redis Test App",
    description="Тестовое приложение для проверки работы Redis клиента",
    version="1.0.0",
    lifespan=test_redis_connection_lifespan,
)

app.include_router(redis_router)

