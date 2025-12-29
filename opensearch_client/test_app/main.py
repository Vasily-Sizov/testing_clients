from fastapi import FastAPI

from my_opensearch_client.endpoint.routes import opensearch_router

app = FastAPI(
    title="OpenSearch Test App",
    description="Тестовое приложение для проверки работы OpenSearch клиента",
    version="1.0.0",
)

app.include_router(opensearch_router)
