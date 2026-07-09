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
        Инициализирует MLLP-фреймер.

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
            Собранное MLLP-сообщение либо None.
        """
        start = data.find(self.START_BYTES)
        end = data.find(self.END_BYTES)

        if start != -1 and end != -1:
            logger.debug("Received complete MLLP message")

            return MLLPMessage(
                message=data[start + len(self.START_BYTES):end],
            )

        if start != -1:
            await self._handle_start(data, start)
            return None

        if end != -1 and self._state is FramerState.RECEIVING:
            return await self._handle_end(data, end)

        if self._state is FramerState.RECEIVING:
            self._append_fragment(data)

        return None

    async def _handle_start(
        self,
        data: bytes,
        start: int,
    ) -> None:
        """
        Начинает сборку нового MLLP-сообщения.
        """
        logger.debug("Detected MLLP message start")

        await self._cancel_timer()

        self._reset()

        self._state = FramerState.RECEIVING
        self._buffer.extend(data[start + len(self.START_BYTES):])

        self._timer_task = asyncio.create_task(self._timeout())

        logger.debug(
            "Started buffering MLLP message ({} byte(s))",
            len(self._buffer),
        )

    async def _handle_end(
        self,
        data: bytes,
        end: int,
    ) -> MLLPMessage:
        """
        Завершает сборку MLLP-сообщения.
        """
        logger.debug("Detected MLLP message end")

        self._buffer.extend(data[:end])

        await self._cancel_timer()

        message = bytes(self._buffer)

        logger.debug(
            "Assembled MLLP message ({} byte(s))",
            len(message),
        )

        self._reset()

        return MLLPMessage(message)

    def _append_fragment(
        self,
        data: bytes,
    ) -> None:
        """
        Добавляет очередной фрагмент сообщения в буфер.
        """
        self._buffer.extend(data)

        logger.trace(
            "Buffered {} byte(s), total {} byte(s)",
            len(data),
            len(self._buffer),
        )

    async def _timeout(self) -> None:
        """
        Контролирует максимальное время получения сообщения.
        """
        try:
            await asyncio.sleep(self._receive_timeout)

            logger.warning(
                "MLLP receive timeout exceeded ({} second(s))",
                self._receive_timeout,
            )

            self._reset()

        except asyncio.CancelledError:
            logger.trace("Receive timer cancelled")

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
        Сбрасывает внутреннее состояние фреймера.
        """
        self._buffer.clear()
        self._state = FramerState.IDLE