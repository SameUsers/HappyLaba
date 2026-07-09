import asyncio

from loguru import logger

from core.components.framer import HL7Framer
from core.config.tcp import DeviceSessionConfig
from core.domain.devices_types import DevicesTypeEnum
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
                Объект asyncio StreamReader для чтения данных из TCP-потока.

            writer:
                Объект asyncio StreamWriter для записи данных в TCP-поток
                и получения информации о соединении.

            config:
                Конфигурация сессии.

        Raises:
            InvalidPeerInfo:
                Если невозможно получить информацию
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
        """
        logger.debug(
            "Session {}:{} started",
            self.host,
            self.port,
        )

        try:
            await self._receive_loop(channel_type)

        except asyncio.CancelledError:
            logger.debug(
                "Session {}:{} cancelled",
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

    async def _receive_loop(
        self,
        channel_type: DevicesTypeEnum,
    ) -> None:
        """
        Выполняет цикл приема данных из TCP-потока.

        Ожидает входящие данные от удаленной стороны и обрабатывает
        их до момента закрытия соединения, отмены задачи или сброса
        соединения.
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

                logger.trace(
                    "Received {} byte(s) from {}:{}",
                    len(chunk),
                    self.host,
                    self.port,
                )

                message = await self._framer.frame(chunk)
                self._log_received_message(message, channel_type)

        except asyncio.CancelledError:
            raise

        except ConnectionResetError:
            logger.debug(
                "Connection reset by peer {}:{}",
                self.host,
                self.port,
            )
            raise

    def _log_received_message(
        self,
        message: str | None,
        channel_type: DevicesTypeEnum,
    ) -> None:
        """
        Выполняет логирование успешно собранного сообщения.
        """
        if message is None:
            return

        logger.debug(
            "Received message from channel '{}': {}",
            channel_type,
            message,
        )

    async def _close(self) -> None:
        """
        Корректно закрывает TCP-соединение и освобождает сетевые ресурсы.

        Повторный вызов безопасен и не выполняет закрытие,
        если соединение уже находится в процессе завершения.
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
