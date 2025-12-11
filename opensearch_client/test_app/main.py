from fastapi import FastAPI

from routes import router

app = FastAPI(
    title="OpenSearch Test App",
    description="Тестовое приложение для проверки работы OpenSearch клиента",
    version="1.0.0",
)

app.include_router(router)
