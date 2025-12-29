from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from my_artemis_client.client.client import ArtemisClient
from my_artemis_client.endpoint.entities import SendMessageRequest
from my_artemis_client.endpoint.lifespan import artemis_lifespan

artemis_router = APIRouter(prefix="/artemis", tags=["artemis"], lifespan=artemis_lifespan)


def get_artemis_client(request: Request) -> ArtemisClient:
    """
    Dependency для получения ArtemisClient из state приложения.

    :param request: FastAPI request
    :return: ArtemisClient
    :raises HTTPException: если клиент не найден в state
    """
    client = getattr(request.app.state, "artemis_client", None)
    if client is None:
        raise HTTPException(
            status_code=500,
            detail="Artemis client not initialized",
        )
    return client


# Эндпоинты
@artemis_router.post("/send")
async def send_message(
    request: SendMessageRequest,
    client: ArtemisClient = Depends(get_artemis_client),
) -> dict[str, Any]:
    """
    Отправляет сообщение в указанную очередь Artemis.
    """
    success = await client.send_message(queue=request.queue, body=request.body)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send message to queue '{request.queue}'",
        )
    
    return {
        "queue": request.queue,
        "message": "Message sent successfully",
        "body": request.body,
    }

