from fastapi import FastAPI

from routes import router

app = FastAPI(
    title="Redis Test App",
    description="Тестовое приложение для проверки работы Redis клиента",
    version="1.0.0",
)

app.include_router(router)
