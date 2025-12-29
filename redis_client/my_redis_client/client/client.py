"""
Клиент-обёртка над Redis для работы с очередями.

Содержит только методы работы с Redis очередями.
Не управляет соединением и не знает о lifecycle приложения.
"""
import json
from typing import Optional, Any, Union

from redis.asyncio import Redis


class RedisClient:
    """
    Клиент-обёртка над Redis для работы с очередями.

    Содержит только методы работы с Redis.
    Не управляет соединением и не знает о lifecycle приложения.
    """

    def __init__(self, connection: Redis) -> None:
        """
        Инициализирует клиент готовым соединением Redis.

        :param connection: Redis соединение
        """
        self._conn = connection

    async def ping(self) -> bool:
        """
        Проверяет доступность Redis.

        :return: True, если Redis доступен
        """
        try:
            result = await self._conn.ping()
            return result is True
        except Exception:
            return False

    async def info(self, section: Optional[str] = None) -> dict[str, Any]:
        """
        Возвращает информацию о Redis сервере.

        :param section: опциональная секция информации (server, clients, memory, etc.)
        :return: словарь с информацией о сервере
        """
        info_result = await self._conn.info(section=section)
        
        # В новых версиях redis может возвращать dict напрямую
        if isinstance(info_result, dict):
            return info_result
        
        # Старые версии возвращают bytes или строку, парсим её в словарь
        if isinstance(info_result, bytes):
            info_str = info_result.decode("utf-8")
        else:
            info_str = str(info_result)
        
        result: dict[str, Any] = {}
        for line in info_str.split("\r\n"):
            if line and not line.startswith("#") and ":" in line:
                key, value = line.split(":", 1)
                # Пытаемся преобразовать значение в число, если возможно
                try:
                    if "." in value:
                        result[key] = float(value)
                    else:
                        result[key] = int(value)
                except ValueError:
                    result[key] = value
        return result

    # ========================================================================
    # Методы для работы с очередями
    # ========================================================================

    async def queue_push(
        self,
        queue_name: str,
        message: Union[str, bytes, dict, list],
        side: str = "left",
    ) -> int:
        """
        Добавляет сообщение в очередь.

        :param queue_name: имя очереди
        :param message: сообщение для добавления (строка, bytes, dict или list)
        :param side: сторона добавления - "left" (LPUSH) или "right" (RPUSH)
        :return: новый размер очереди после добавления
        """
        # Преобразуем сообщение в строку для хранения
        if isinstance(message, (dict, list)):
            message_str = json.dumps(message)
        elif isinstance(message, bytes):
            message_str = message.decode("utf-8")
        else:
            message_str = str(message)

        if side == "left":
            return await self._conn.lpush(queue_name, message_str)
        else:
            return await self._conn.rpush(queue_name, message_str)

    async def queue_pop(
        self,
        queue_name: str,
        side: str = "right",
    ) -> Optional[str]:
        """
        Извлекает сообщение из очереди (неблокирующая операция).

        :param queue_name: имя очереди
        :param side: сторона извлечения - "left" (LPOP) или "right" (RPOP)
        :return: сообщение или None, если очередь пуста
        """
        if side == "left":
            result = await self._conn.lpop(queue_name)
        else:
            result = await self._conn.rpop(queue_name)

        if result is None:
            return None

        # Возвращаем как строку (decode_responses может быть False)
        if isinstance(result, bytes):
            return result.decode("utf-8")
        return result

    async def queue_blocking_pop(
        self,
        queue_names: Union[str, list[str]],
        timeout: int = 0,
        side: str = "right",
    ) -> Optional[tuple[str, str]]:
        """
        Извлекает сообщение из очереди (блокирующая операция).

        Блокирует выполнение до получения сообщения или истечения таймаута.

        :param queue_names: имя очереди или список имён очередей
        :param timeout: таймаут в секундах (0 = бесконечно)
        :param side: сторона извлечения - "left" (BLPOP) или "right" (BRPOP)
        :return: кортеж (имя_очереди, сообщение) или None при таймауте
        """
        if isinstance(queue_names, str):
            queue_names = [queue_names]

        if side == "left":
            result = await self._conn.blpop(queue_names, timeout=timeout)
        else:
            result = await self._conn.brpop(queue_names, timeout=timeout)

        if result is None:
            return None

        queue_name, message = result

        # Декодируем, если нужно
        if isinstance(queue_name, bytes):
            queue_name = queue_name.decode("utf-8")
        if isinstance(message, bytes):
            message = message.decode("utf-8")

        return (queue_name, message)

    async def queue_size(self, queue_name: str) -> int:
        """
        Возвращает размер очереди (количество элементов).

        :param queue_name: имя очереди
        :return: количество элементов в очереди
        """
        return await self._conn.llen(queue_name)

    async def queue_peek(
        self,
        queue_name: str,
        count: int = 1,
        side: str = "left",
    ) -> list[str]:
        """
        Просматривает элементы очереди без их удаления.

        :param queue_name: имя очереди
        :param count: количество элементов для просмотра
        :param side: сторона - "left" (начало) или "right" (конец)
        :return: список элементов
        """
        if side == "left":
            # LRANGE 0 count-1
            result = await self._conn.lrange(queue_name, 0, count - 1)
        else:
            # LRANGE -count -1
            result = await self._conn.lrange(queue_name, -count, -1)

        # Декодируем, если нужно
        decoded: list[str] = []
        for item in result:
            if isinstance(item, bytes):
                decoded.append(item.decode("utf-8"))
            else:
                decoded.append(item)

        return decoded

    async def queue_clear(self, queue_name: str) -> bool:
        """
        Очищает очередь (удаляет все элементы).

        :param queue_name: имя очереди
        :return: True, если очередь была очищена
        """
        deleted = await self._conn.delete(queue_name)
        return deleted > 0

    async def queue_exists(self, queue_name: str) -> bool:
        """
        Проверяет существование очереди (есть ли в ней элементы).

        :param queue_name: имя очереди
        :return: True, если очередь существует и не пуста
        """
        size = await self.queue_size(queue_name)
        return size > 0

    async def queue_list_all(self, pattern: str = "*") -> list[str]:
        """
        Возвращает список всех очередей, соответствующих паттерну.

        :param pattern: паттерн для поиска (например, "queue:*")
        :return: список имён очередей
        """
        keys = await self._conn.keys(pattern)
        # Декодируем, если нужно
        decoded: list[str] = []
        for key in keys:
            if isinstance(key, bytes):
                decoded.append(key.decode("utf-8"))
            else:
                decoded.append(key)
        return decoded

