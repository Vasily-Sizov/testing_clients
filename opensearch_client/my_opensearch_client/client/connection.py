from typing import Sequence, Optional
from opensearchpy import AsyncOpenSearch


def create_opensearch_connection(
    hosts: Sequence[str],
    username: Optional[str] = None,
    password: Optional[str] = None,
    timeout: int = 30,
    max_retries: int = 3,
    retry_on_timeout: bool = True,
    verify_certs: bool = True,
) -> AsyncOpenSearch:
    """
    Создаёт соединение с OpenSearch.

    Используется на уровне lifecycle приложения (lifespan).
    Возвращаемый объект должен жить столько же, сколько живёт приложение.

    :param hosts: список хостов OpenSearch
    :param username: имя пользователя для basic auth
    :param password: пароль для basic auth
    :param timeout: таймаут запросов
    :param max_retries: количество повторов
    :param retry_on_timeout: повторять ли запрос при таймауте
    :param verify_certs: проверять ли SSL-сертификаты
    :return: AsyncOpenSearch клиент
    """
    return AsyncOpenSearch(
        hosts=list(hosts),
        http_auth=(username, password) if username else None,
        timeout=timeout,
        max_retries=max_retries,
        retry_on_timeout=retry_on_timeout,
        verify_certs=verify_certs,
    )
