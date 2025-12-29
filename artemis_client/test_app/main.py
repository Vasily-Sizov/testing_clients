from fastapi import FastAPI

from my_artemis_client.endpoint.routes import artemis_router

app = FastAPI(
    title="Artemis Test App",
    description="Тестовое приложение для проверки работы Artemis клиента",
    version="1.0.0",
)

app.include_router(artemis_router)

