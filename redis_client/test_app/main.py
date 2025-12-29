from fastapi import FastAPI

from my_redis_client.endpoint.routes import redis_router

app = FastAPI(
    title="Redis Test App",
    description="Тестовое приложение для проверки работы Redis клиента",
    version="1.0.0",
)

app.include_router(redis_router)
