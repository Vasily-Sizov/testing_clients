from fastapi import FastAPI

from my_s3_client.endpoint.routes import s3_router

app = FastAPI(
    title="S3 Test App",
    description="Тестовое приложение для проверки работы S3 клиента",
    version="1.0.0",
)

app.include_router(s3_router)
