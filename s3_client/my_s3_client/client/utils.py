"""
Утилиты для работы с S3.
"""
import os
import logging
from my_s3_client.client.client import S3Client

logger = logging.getLogger(__name__)


async def sync_dir(
    client: S3Client,
    bucket_name: str,
    s3_prefix: str,
    local_path: str,
) -> None:
    """
    Синхронизирует директорию из S3 в локальную файловую систему.

    :param client: экземпляр S3Client
    :param bucket_name: имя bucket'а
    :param s3_prefix: префикс пути на S3
    :param local_path: локальный путь для сохранения файлов
    """
    objects = await client.list_objects(bucket_name, prefix=s3_prefix, max_keys=10000)
    
    for obj in objects:
        s3_key = obj["key"]
        # Вычисляем относительный путь от префикса
        if s3_prefix:
            relative_path = os.path.relpath(s3_key, s3_prefix)
        else:
            relative_path = s3_key
        
        local_file_path = os.path.join(local_path, relative_path)
        local_file_dir = os.path.dirname(local_file_path)
        
        # Если директория существует как файл, удаляем его
        if local_file_dir and os.path.isfile(local_file_dir):
            os.remove(local_file_dir)
        
        # Создаём директорию, если её нет
        if local_file_dir:
            os.makedirs(local_file_dir, exist_ok=True)
        
        try:
            logger.debug(f" -> downloading {s3_key} to {local_file_path}")
            # Пропускаем директории (ключи, заканчивающиеся на /)
            if not s3_key.endswith('/'):
                await client.download_object_to_file(
                    bucket_name=bucket_name,
                    object_key=s3_key,
                    file_path=local_file_path,
                )
        except Exception as e:
            logger.info(f"sync dir {s3_prefix} {local_path} ! Failed: {str(e)}")

