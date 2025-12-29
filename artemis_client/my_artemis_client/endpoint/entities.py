"""
Модели данных для API запросов Artemis.

Содержит Pydantic модели для валидации входящих запросов.
"""
from pydantic import BaseModel, Field


class SendMessageRequest(BaseModel):
    """
    Запрос на отправку сообщения в очередь Artemis.

    :param queue: название очереди в Artemis (например, "chat.out", "email.out")
    :param body: тело сообщения (строка)
    """

    queue: str = Field(..., description="Название очереди в Artemis")
    body: str = Field(..., description="Тело сообщения для отправки")

