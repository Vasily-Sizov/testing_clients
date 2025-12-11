from fastapi import FastAPI

from routes import router

app = FastAPI(
    title="S3 Test App",
    description="Тестовое приложение для проверки работы S3 клиента",
    version="1.0.0",
)

app.include_router(router)

