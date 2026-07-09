import asyncio
from enum import Enum, auto

from loguru import logger

from core.domain.schemas.mllp_message import MLLPMessage


class FramerState(Enum):
    """
    Возможные состояния MLLP-фреймера.
    """

    IDLE = auto()
    RECEIVING = auto()


class HL7Framer:
    """
    Фреймер MLLP сообщений.

    Основная задача данного класса — собрать целое HL7 сообщение из
    последовательности TCP-фрагментов.

    Допущения реализации:

        - Одно TCP-соединение обслуживает одно устройство.
        - Устройство отправляет сообщения строго последовательно.
        - Следующее сообщение не начинается, пока полностью не закончено
          предыдущее.
        - Устройство корректно использует MLLP-обрамление.
        - Нарушение этих правил считается ошибкой оборудования.

    Если сообщение не было получено полностью за установленное время,
    внутреннее состояние фреймера сбрасывается.
    """

    START_BYTES = b"\x0b"
    END_BYTES = b"\x1c\x0d"

    def __init__(self, receive_timeout: int = 30) -> None:
        """
        Инициализация фреймера.

        Args:
            receive_timeout:
                Максимальное время ожидания завершения сообщения.
        """
        self._buffer = bytearray()
        self._state = FramerState.IDLE
        self._receive_timeout = receive_timeout
        self._timer_task: asyncio.Task | None = None

    async def frame(self, data: bytes) -> MLLPMessage | None:
        """
        Обрабатывает очередной TCP-фрагмент.

        Args:
            data:
                Полученные из TCP-соединения байты.

        Returns:
            MLLPMessage при успешной сборке сообщения,
            иначе None.
        """
        start = data.find(self.START_BYTES)
        end = data.find(self.END_BYTES)
        if start != -1 and end != -1:
            logger.debug("Complete MLLP message received.")
            return MLLPMessage(
                message=data[start + len(self.START_BYTES):end]
            )
        if start != -1:
            logger.debug("MLLP message start detected.")
            self._reset()
            self._state = FramerState.RECEIVING
            self._buffer.extend(
                data[start + len(self.START_BYTES):]
            )
            self._timer_task = asyncio.create_task(
                self._timeout()
            )
            logger.debug(
                "Receiving started. Buffered {} bytes.",
                len(self._buffer),
            )
            return None
        if end != -1 and self._state is FramerState.RECEIVING:
            logger.debug("MLLP message end detected.")
            self._buffer.extend(data[:end])
            await self._cancel_timer()
            message = bytes(self._buffer)
            logger.debug(
                "MLLP message assembled successfully ({} bytes).",
                len(message),
            )
            self._reset()
            return MLLPMessage(message)
        if self._state is FramerState.RECEIVING:
            self._buffer.extend(data)
            logger.debug(
                "Received message fragment ({} bytes). Total buffered: {} bytes.",
                len(data),
                len(self._buffer),
            )
        return None

    async def _timeout(self) -> None:
        """
        Контролирует максимальное время получения сообщения.
        """
        try:
            await asyncio.sleep(self._receive_timeout)
            logger.error(
                "Message receive timeout exceeded ({} seconds). Resetting framer state.",
                self._receive_timeout,
            )
            self._reset()
        except asyncio.CancelledError:
            logger.debug("Receive timer cancelled.")

    async def _cancel_timer(self) -> None:
        """
        Останавливает таймер ожидания сообщения.
        """
        if self._timer_task is None:
            return
        self._timer_task.cancel()
        try:
            await self._timer_task
        except asyncio.CancelledError:
            pass
        self._timer_task = None

    def _reset(self) -> None:
        """
        Полностью очищает внутреннее состояние фреймера.
        """
        self._buffer.clear()
        self._state = FramerState.IDLE
        self._timer_task = None