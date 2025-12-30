from typing import Optional
from redis.asyncio import Redis


def create_redis_connection(
    host: str = "localhost",
    port: int = 6379,
    db: int = 0,
    username: Optional[str] = None,
    password: Optional[str] = None,
    decode_responses: bool = False,
    socket_timeout: Optional[float] = None,
    socket_connect_timeout: Optional[float] = None,
    retry_on_timeout: bool = True,
    health_check_interval: int = 30,
) -> Redis:
    """
    Создаёт соединение с Redis.

    Используется на уровне lifecycle приложения (lifespan).
    Возвращаемый объект должен жить столько же, сколько живёт приложение.

    :param host: хост Redis сервера
    :param port: порт Redis сервера
    :param db: номер базы данных (0-15)
    :param username: имя пользователя для ACL (Redis 6.0+)
    :param password: пароль для аутентификации
    :param decode_responses: декодировать ли ответы как строки (по умолчанию False - bytes)
    :param socket_timeout: таймаут для операций сокета
    :param socket_connect_timeout: таймаут для подключения
    :param retry_on_timeout: повторять ли запрос при таймауте
    :param health_check_interval: интервал проверки здоровья соединения (секунды)
    :return: Redis клиент
    """
    return Redis(
        host=host,
        port=port,
        db=db,
        username=username,
        password=password,
        decode_responses=decode_responses,
        socket_timeout=socket_timeout,
        socket_connect_timeout=socket_connect_timeout,
        retry_on_timeout=retry_on_timeout,
        health_check_interval=health_check_interval,
    )

