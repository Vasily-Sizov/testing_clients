from typing import Any, Optional
from fastapi import APIRouter, Request, HTTPException, Depends

from client.client import RedisClient
from lifespan import redis_lifespan
from entities import (
    QueuePushRequest,
    QueuePopRequest,
    QueueBlockingPopRequest,
    QueuePeekRequest,
    QueueSizeRequest,
    QueueClearRequest,
    QueueExistsRequest,
)


router = APIRouter(prefix="/redis", tags=["redis"], lifespan=redis_lifespan)


def get_redis_client(request: Request) -> RedisClient:
    """
    Dependency для получения RedisClient из state приложения.

    :param request: FastAPI request
    :return: RedisClient
    :raises HTTPException: если клиент не найден в state
    """
    client = getattr(request.app.state, "redis_client", None)
    if client is None:
        raise HTTPException(
            status_code=500,
            detail="Redis client not initialized",
        )
    return client


# Эндпоинты
@router.get("/ping")
async def ping(
    client: RedisClient = Depends(get_redis_client),
) -> dict[str, bool]:
    """Проверяет доступность Redis."""
    is_available = await client.ping()
    return {"available": is_available}


@router.get("/info")
async def info(
    section: Optional[str] = None,
    client: RedisClient = Depends(get_redis_client),
) -> dict[str, Any]:
    """Возвращает информацию о Redis сервере."""
    return await client.info(section=section)


@router.get("/queues")
async def list_queues(
    pattern: str = "*",
    client: RedisClient = Depends(get_redis_client),
) -> list[str]:
    """Возвращает список всех очередей, соответствующих паттерну."""
    return await client.queue_list_all(pattern=pattern)


# ========================================================================
# Эндпоинты для работы с очередями
# ========================================================================

@router.post("/queues/push")
async def queue_push(
    request: QueuePushRequest,
    client: RedisClient = Depends(get_redis_client),
) -> dict[str, Any]:
    """Добавляет сообщение в очередь."""
    size = await client.queue_push(
        queue_name=request.queue_name,
        message=request.message,
        side=request.side,
    )
    return {
        "queue_name": request.queue_name,
        "size": size,
        "message": "Message added to queue",
    }


@router.post("/queues/pop")
async def queue_pop(
    request: QueuePopRequest,
    client: RedisClient = Depends(get_redis_client),
) -> dict[str, Any]:
    """Извлекает сообщение из очереди (неблокирующая операция)."""
    message = await client.queue_pop(
        queue_name=request.queue_name,
        side=request.side,
    )

    if message is None:
        raise HTTPException(
            status_code=404,
            detail=f"Queue '{request.queue_name}' is empty",
        )

    return {
        "queue_name": request.queue_name,
        "message": message,
    }


@router.post("/queues/blocking-pop")
async def queue_blocking_pop(
    request: QueueBlockingPopRequest,
    client: RedisClient = Depends(get_redis_client),
) -> dict[str, Any]:
    """Извлекает сообщение из очереди (блокирующая операция)."""
    result = await client.queue_blocking_pop(
        queue_names=request.queue_names,
        timeout=request.timeout,
        side=request.side,
    )

    if result is None:
        raise HTTPException(
            status_code=408,
            detail="Timeout: no message received within the specified timeout",
        )

    queue_name, message = result
    return {
        "queue_name": queue_name,
        "message": message,
    }


@router.post("/queues/peek")
async def queue_peek(
    request: QueuePeekRequest,
    client: RedisClient = Depends(get_redis_client),
) -> dict[str, Any]:
    """Просматривает элементы очереди без их удаления."""
    messages = await client.queue_peek(
        queue_name=request.queue_name,
        count=request.count,
        side=request.side,
    )

    return {
        "queue_name": request.queue_name,
        "messages": messages,
        "count": len(messages),
    }


@router.post("/queues/size")
async def queue_size(
    request: QueueSizeRequest,
    client: RedisClient = Depends(get_redis_client),
) -> dict[str, Any]:
    """Возвращает размер очереди (количество элементов)."""
    size = await client.queue_size(request.queue_name)
    return {
        "queue_name": request.queue_name,
        "size": size,
    }


@router.post("/queues/clear")
async def queue_clear(
    request: QueueClearRequest,
    client: RedisClient = Depends(get_redis_client),
) -> dict[str, str]:
    """Очищает очередь (удаляет все элементы)."""
    cleared = await client.queue_clear(request.queue_name)
    if cleared:
        return {
            "queue_name": request.queue_name,
            "message": "Queue cleared successfully",
        }
    else:
        return {
            "queue_name": request.queue_name,
            "message": "Queue was already empty or does not exist",
        }


@router.post("/queues/exists")
async def queue_exists(
    request: QueueExistsRequest,
    client: RedisClient = Depends(get_redis_client),
) -> dict[str, Any]:
    """Проверяет существование очереди (есть ли в ней элементы)."""
    exists = await client.queue_exists(request.queue_name)
    return {
        "queue_name": request.queue_name,
        "exists": exists,
    }
