"""
Модели данных для API запросов Redis.

Содержит Pydantic модели для валидации входящих запросов.
"""
from typing import Any, Optional, Union
from pydantic import BaseModel, Field


class QueuePushRequest(BaseModel):
    """
    Запрос на добавление сообщения в очередь.

    :param queue_name: имя очереди
    :param message: сообщение для добавления (может быть строкой, dict, list)
    :param side: сторона добавления - "left" (LPUSH) или "right" (RPUSH)
    """

    queue_name: str = Field(..., description="Имя очереди")
    message: Union[str, dict[str, Any], list[Any]] = Field(
        ...,
        description="Сообщение для добавления",
    )
    side: str = Field(
        "left",
        description="Сторона добавления: 'left' (LPUSH) или 'right' (RPUSH)",
        pattern="^(left|right)$",
    )


class QueuePopRequest(BaseModel):
    """
    Запрос на извлечение сообщения из очереди (неблокирующая операция).

    :param queue_name: имя очереди
    :param side: сторона извлечения - "left" (LPOP) или "right" (RPOP)
    """

    queue_name: str = Field(..., description="Имя очереди")
    side: str = Field(
        "right",
        description="Сторона извлечения: 'left' (LPOP) или 'right' (RPOP)",
        pattern="^(left|right)$",
    )


class QueueBlockingPopRequest(BaseModel):
    """
    Запрос на извлечение сообщения из очереди (блокирующая операция).

    :param queue_names: имя очереди или список имён очередей
    :param timeout: таймаут в секундах (0 = бесконечно, максимум 3600)
    :param side: сторона извлечения - "left" (BLPOP) или "right" (BRPOP)
    """

    queue_names: Union[str, list[str]] = Field(
        ...,
        description="Имя очереди или список имён очередей",
    )
    timeout: int = Field(
        0,
        ge=0,
        le=3600,
        description="Таймаут в секундах (0 = бесконечно)",
    )
    side: str = Field(
        "right",
        description="Сторона извлечения: 'left' (BLPOP) или 'right' (BRPOP)",
        pattern="^(left|right)$",
    )


class QueuePeekRequest(BaseModel):
    """
    Запрос на просмотр элементов очереди без удаления.

    :param queue_name: имя очереди
    :param count: количество элементов для просмотра
    :param side: сторона - "left" (начало) или "right" (конец)
    """

    queue_name: str = Field(..., description="Имя очереди")
    count: int = Field(1, ge=1, le=1000, description="Количество элементов")
    side: str = Field(
        "left",
        description="Сторона: 'left' (начало) или 'right' (конец)",
        pattern="^(left|right)$",
    )


class QueueSizeRequest(BaseModel):
    """
    Запрос на получение размера очереди.

    :param queue_name: имя очереди
    """

    queue_name: str = Field(..., description="Имя очереди")


class QueueClearRequest(BaseModel):
    """
    Запрос на очистку очереди.

    :param queue_name: имя очереди
    """

    queue_name: str = Field(..., description="Имя очереди")


class QueueExistsRequest(BaseModel):
    """
    Запрос на проверку существования очереди.

    :param queue_name: имя очереди
    """

    queue_name: str = Field(..., description="Имя очереди")

