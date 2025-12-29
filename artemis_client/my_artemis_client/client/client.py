"""
Клиент-обёртка над Artemis для отправки сообщений в очереди.

Содержит только методы работы с Artemis.
Не управляет соединением напрямую, использует Container для каждой операции.
"""
from typing import Optional
from proton import Message
from proton.handlers import MessagingHandler
from proton.reactor import Container
import logging
import asyncio

logger = logging.getLogger(__name__)


class _OneShotSender(MessagingHandler):
    """
    Вспомогательный класс для одноразовой отправки сообщения
    в указанную очередь Artemis.
    """

    def __init__(self, url: str, queue: str, body: str):
        super().__init__()
        self.url = url
        self.queue = queue
        self.body = body
        self.sent = False
        self.error: Optional[str] = None
        self.sender = None
        self.connection = None

    def on_start(self, event):
        """
        Устанавливает соединение и создаёт sender.
        """
        try:
            logger.debug(f"Подключение к {self.url}, очередь: {self.queue}")
            self.connection = event.container.connect(self.url)
            self.sender = event.container.create_sender(self.connection, self.queue)
            logger.debug("Соединение и sender созданы")
        except Exception as e:
            self.error = str(e)
            logger.error(f"Ошибка при создании соединения: {e}")
            event.container.stop()

    def on_connection_opened(self, event):
        """Вызывается когда соединение открыто."""
        logger.debug("Соединение открыто")

    def on_link_opened(self, event):
        """Вызывается когда линк открыт."""
        logger.debug(f"Линк открыт: {event.link}")

    def on_sendable(self, event):
        """Вызывается когда sender готов к отправке - отправляем сообщение."""
        if event.sender and not self.sent:
            try:
                logger.info(f"Отправка сообщения в Artemis очередь {self.queue}: {self.body}")
                event.sender.send(Message(body=self.body))
                self.sent = True
                logger.debug("Сообщение отправлено, ожидаем подтверждения")
            except Exception as e:
                self.error = str(e)
                logger.error(f"Ошибка при отправке сообщения: {e}")
                if self.connection:
                    self.connection.close()
                event.container.stop()

    def on_accepted(self, event):
        """Вызывается когда сообщение принято брокером."""
        logger.debug("Сообщение принято брокером")
        if self.connection:
            self.connection.close()
        event.container.stop()

    def on_rejected(self, event):
        """Вызывается когда сообщение отклонено."""
        self.error = f"Сообщение отклонено: {event.delivery.remote_state}"
        logger.error(self.error)
        if self.connection:
            self.connection.close()
        event.container.stop()

    def on_connection_closed(self, event):
        """Вызывается когда соединение закрыто."""
        logger.debug("Соединение закрыто")

    def on_transport_error(self, event):
        """Вызывается при ошибке транспорта."""
        self.error = f"Transport error: {event.transport.condition}"
        logger.error(self.error)
        event.container.stop()


class ArtemisClient:
    """
    Клиент-обёртка над Artemis для отправки сообщений в очереди.

    Содержит только методы работы с Artemis.
    Каждая отправка создаёт временное соединение через Container.
    """

    def __init__(self, connection_url: str) -> None:
        """
        Инициализирует клиент с URL для подключения к Artemis.

        :param connection_url: URL строка для подключения к Artemis
                              (например, "amqp://user:pass@localhost:61616")
        """
        self._connection_url = connection_url

    async def send_message(self, queue: str, body: str) -> bool:
        """
        Отправляет одно сообщение в указанную очередь Artemis.

        :param queue: название очереди в Artemis (например, "chat.out", "email.out")
        :param body: тело сообщения (строка)
        :return: True, если сообщение успешно отправлено, False в противном случае
        """
        sender = _OneShotSender(self._connection_url, queue, body)
        
        try:
            # Container.run() блокирующий, поэтому оборачиваем в executor для async
            loop = asyncio.get_event_loop()
            
            # Запускаем Container в отдельном потоке, чтобы не блокировать event loop
            def run_container():
                Container(sender).run()
            
            await loop.run_in_executor(None, run_container)
            
            if sender.error:
                logger.error(f"Ошибка отправки: {sender.error}")
                return False
                
            return sender.sent
            
        except Exception as e:
            logger.error(f"Исключение при отправке сообщения: {e}")
            return False

    def send_message_sync(self, queue: str, body: str) -> bool:
        """
        Отправляет одно сообщение в указанную очередь Artemis (синхронная версия).

        :param queue: название очереди в Artemis (например, "chat.out", "email.out")
        :param body: тело сообщения (строка)
        :return: True, если сообщение успешно отправлено, False в противном случае
        """
        sender = _OneShotSender(self._connection_url, queue, body)
        
        try:
            Container(sender).run()
            
            if sender.error:
                logger.error(f"Ошибка отправки: {sender.error}")
                return False
                
            return sender.sent
            
        except Exception as e:
            logger.error(f"Исключение при отправке сообщения: {e}")
            return False

