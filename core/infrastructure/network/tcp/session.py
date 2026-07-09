import asyncio

from loguru import logger
from core.components.framer import HL7Framer
from core.domain.devices_types import DevicesTypeEnum
from core.config.tcp import DeviceSessionConfig
from core.infrastructure.network.tcp.exception import (
    InvalidPeerInfo,
    SessionRemoteClose,
)


class TCPSession:
    """
    Представляет активное TCP-соединение с клиентом.

    Ответственность:
    - чтение и запись данных через TCP-поток;
    - хранение состояния текущего соединения;
    - обработка входящих данных от удаленной стороны;
    - корректное завершение соединения и освобождение ресурсов.

    TCPSession управляет жизненным циклом одного соединения,
    но не отвечает за регистрацию и управление множеством сессий.
    """

    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        config: DeviceSessionConfig,
        framer: HL7Framer,
    ) -> None:
        """
        Инициализирует объект TCP-сессии поверх существующего соединения.

        Args:
            reader:
                Объект asyncio StreamReader для чтения данных
                из TCP-потока.

            writer:
                Объект asyncio StreamWriter для записи данных
                в TCP-поток и получения информации о соединении.

            config:
                Конфигурация сессии, содержащая параметры
                выполнения и обработки соединения.

        Raises:
            InvalidPeerInfo:
                Возникает, если невозможно получить информацию
                об удаленной стороне соединения.
        """
        self._reader = reader
        self._writer = writer
        self._framer = framer
        self._read_size = config.read_size

        peer = self._writer.get_extra_info("peername")
        if peer is None or not isinstance(peer, tuple):
            logger.error("Failed to retrieve remote peer information")
            raise InvalidPeerInfo("Remote peer information is unavailable.")

        self._host, self._port = peer

        logger.debug(
            "TCP session created for {}:{}",
            self.host,
            self.port,
        )

    async def run(self, channel_type: DevicesTypeEnum) -> None:
        """
        Запускает основной цикл обработки TCP-соединения.

        Выполняет прием и обработку входящих данных до момента
        закрытия соединения удаленной стороной, отмены задачи
        или возникновения необработанной ошибки.

        Гарантирует освобождение ресурсов соединения после завершения
        работы сессии.

        Raises:
            asyncio.CancelledError:
                Пробрасывается при запросе отмены задачи во время
                завершения работы сервера.

            SessionRemoteClose:
                Пробрасывается при закрытии соединения удаленной стороной.

            Exception:
                Пробрасывается при необработанных ошибках обработки сессии.
        """
        logger.debug(
            "Session {}:{} started",
            self.host,
            self.port,
        )

        try:
            await self._receive_loop(channel_type=channel_type)

        except asyncio.CancelledError:
            logger.debug(
                "Session {}:{} received cancellation request",
                self.host,
                self.port,
            )
            raise

        except SessionRemoteClose:
            logger.debug(
                "Remote peer {}:{} closed the connection",
                self.host,
                self.port,
            )
            raise

        except Exception:
            logger.exception(
                "Unhandled exception in session {}:{}",
                self.host,
                self.port,
            )
            raise
        finally:
            await self._close()

    async def _receive_loop(self, channel_type: DevicesTypeEnum) -> None:
        """
        Выполняет цикл приема данных из TCP-потока.

        Ожидает входящие данные от удаленной стороны и обрабатывает
        их до момента закрытия соединения, отмены задачи или сброса
        соединения.

        Raises:
            asyncio.CancelledError:
                Пробрасывается при отмене задачи во время завершения
                работы сессии.

            SessionRemoteClose:
                Возникает при закрытии соединения удаленной стороной.

            ConnectionResetError:
                Возникает при принудительном сбросе соединения удаленной
                стороной.
        """
        logger.debug(
            "Receive loop started for {}:{}",
            self.host,
            self.port,
        )
        try:
            while True:
                chunk = await self._reader.read(self.read_size)
                if not chunk:
                    raise SessionRemoteClose
                message = await self._framer.frame(chunk)
                if message:
                    logger.debug("Recieved message {} from {}", message, channel_type)
                logger.trace(
                    "Received {} bytes from {}:{}",
                    len(chunk),
                    self.host,
                    self.port,
                )

        except asyncio.CancelledError:
            raise
        except ConnectionResetError:
            logger.debug(
                "Connection reset by peer {}:{}",
                self.host,
                self.port,
            )
            raise

    async def _close(self) -> None:
        """
        Корректно закрывает TCP-соединение и освобождает сетевые ресурсы.

        Проверяет состояние соединения, инициирует закрытие writer
        и ожидает полного завершения закрытия соединения.

        Повторный вызов безопасен и не выполняет закрытие, если
        соединение уже находится в процессе завершения.
        """
        if self._writer.is_closing():
            logger.trace(
                "Session {}:{} is already closing",
                self.host,
                self.port,
            )
            return
        logger.debug(
            "Closing session {}:{}",
            self.host,
            self.port,
        )

        self._writer.close()
        await self._writer.wait_closed()

        logger.info(
            "Session {}:{} closed",
            self.host,
            self.port,
        )

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @property
    def read_size(self) -> int:
        return self._read_size
