import base64
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from my_s3_client.client.client import S3Client
from my_s3_client.endpoint.entities import (
    CopyObjectRequest,
    CreateBucketRequest,
    DeleteBucketRequest,
    DeleteObjectRequest,
    DownloadObjectRequest,
    GeneratePresignedUrlRequest,
    GetObjectMetadataRequest,
    ListObjectsRequest,
    ObjectExistsRequest,
    UploadObjectRequest,
)
from my_s3_client.endpoint.lifespan import s3_lifespan

s3_router = APIRouter(prefix="/s3", tags=["s3"], lifespan=s3_lifespan)


def get_s3_client(request: Request) -> S3Client:
    """
    Dependency для получения S3Client из state приложения.

    :param request: FastAPI request
    :return: S3Client
    :raises HTTPException: если клиент не найден в state
    """
    client = getattr(request.app.state, "s3_client", None)
    if client is None:
        raise HTTPException(
            status_code=500,
            detail="S3 client not initialized",
        )
    return client


# Эндпоинты
@s3_router.get("/ping")
async def ping(
    client: S3Client = Depends(get_s3_client),
) -> dict[str, bool]:
    """Проверяет доступность S3."""
    is_available = await client.ping()
    return {"available": is_available}


@s3_router.get("/buckets")
async def list_buckets(
    client: S3Client = Depends(get_s3_client),
) -> list[dict[str, str]]:
    """Возвращает список всех bucket'ов."""
    return await client.list_buckets()


@s3_router.post("/buckets/exists")
async def bucket_exists(
    bucket_name: str,
    client: S3Client = Depends(get_s3_client),
) -> dict[str, Any]:
    """Проверяет существование bucket'а."""
    exists = await client.bucket_exists(bucket_name)
    return {"bucket_name": bucket_name, "exists": exists}


@s3_router.post("/buckets/create")
async def create_bucket(
    request: CreateBucketRequest,
    client: S3Client = Depends(get_s3_client),
) -> dict[str, str]:
    """Создаёт bucket."""
    return await client.create_bucket(
        bucket_name=request.bucket_name,
        region=request.region,
    )


@s3_router.post("/buckets/delete")
async def delete_bucket(
    request: DeleteBucketRequest,
    client: S3Client = Depends(get_s3_client),
) -> dict[str, str]:
    """Удаляет bucket (только если он пуст)."""
    return await client.delete_bucket(request.bucket_name)


# ========================================================================
# Эндпоинты для работы с объектами
# ========================================================================


@s3_router.post("/objects/upload")
async def upload_object(
    request: UploadObjectRequest,
    client: S3Client = Depends(get_s3_client),
) -> dict[str, Any]:
    """Загружает объект в S3."""
    # Декодируем base64 данные
    try:
        data = base64.b64decode(request.data)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid base64 data: {str(e)}",
        )

    return await client.upload_object(
        bucket_name=request.bucket_name,
        object_key=request.object_key,
        data=data,
        content_type=request.content_type,
        metadata=request.metadata,
    )


@s3_router.post("/objects/download")
async def download_object(
    request: DownloadObjectRequest,
    client: S3Client = Depends(get_s3_client),
) -> Response:
    """Скачивает объект из S3."""
    try:
        data = await client.download_object(
            bucket_name=request.bucket_name,
            object_key=request.object_key,
        )
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Object not found: {str(e)}",
        )

    return Response(
        content=data,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{request.object_key.split("/")[-1]}"',
        },
    )


@s3_router.post("/objects/delete")
async def delete_object(
    request: DeleteObjectRequest,
    client: S3Client = Depends(get_s3_client),
) -> dict[str, str]:
    """Удаляет объект из S3."""
    return await client.delete_object(
        bucket_name=request.bucket_name,
        object_key=request.object_key,
    )


@s3_router.post("/objects/exists")
async def object_exists(
    request: ObjectExistsRequest,
    client: S3Client = Depends(get_s3_client),
) -> dict[str, Any]:
    """Проверяет существование объекта."""
    exists = await client.object_exists(
        bucket_name=request.bucket_name,
        object_key=request.object_key,
    )
    return {
        "bucket_name": request.bucket_name,
        "object_key": request.object_key,
        "exists": exists,
    }


@s3_router.post("/objects/list")
async def list_objects(
    request: ListObjectsRequest,
    client: S3Client = Depends(get_s3_client),
) -> dict[str, Any]:
    """Возвращает список объектов в bucket'е."""
    objects = await client.list_objects(
        bucket_name=request.bucket_name,
        prefix=request.prefix,
        max_keys=request.max_keys,
    )
    return {
        "bucket_name": request.bucket_name,
        "prefix": request.prefix,
        "objects": objects,
        "count": len(objects),
    }


@s3_router.post("/objects/metadata")
async def get_object_metadata(
    request: GetObjectMetadataRequest,
    client: S3Client = Depends(get_s3_client),
) -> dict[str, Any]:
    """Возвращает метаданные объекта."""
    try:
        return await client.get_object_metadata(
            bucket_name=request.bucket_name,
            object_key=request.object_key,
        )
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Object not found: {str(e)}",
        )


@s3_router.post("/objects/copy")
async def copy_object(
    request: CopyObjectRequest,
    client: S3Client = Depends(get_s3_client),
) -> dict[str, str]:
    """Копирует объект в S3."""
    return await client.copy_object(
        source_bucket=request.source_bucket,
        source_key=request.source_key,
        dest_bucket=request.dest_bucket,
        dest_key=request.dest_key,
    )


@s3_router.post("/objects/presigned-url")
async def generate_presigned_url(
    request: GeneratePresignedUrlRequest,
    client: S3Client = Depends(get_s3_client),
) -> dict[str, str]:
    """Генерирует presigned URL для доступа к объекту."""
    url = await client.generate_presigned_url(
        bucket_name=request.bucket_name,
        object_key=request.object_key,
        expiration=request.expiration,
        method=request.method,
    )
    return {
        "bucket_name": request.bucket_name,
        "object_key": request.object_key,
        "url": url,
        "expiration": request.expiration,
    }
