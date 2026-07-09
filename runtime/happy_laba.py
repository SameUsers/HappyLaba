import asyncio

from loguru import logger

from bootstrap import AppBuilder
from core.infrastructure.network.tcp.server import TCPChannel


class HappyLaba:
    """
    Управляет жизненным циклом приложения.

    Ответственность:
    - создание TCP-каналов;
    - запуск каналов;
    - мониторинг их состояния;
    - автоматический перезапуск завершившихся каналов;
    - корректное завершение работы приложения.
    """

    def __init__(self) -> None:
        self._builder = AppBuilder()
        self._channels: list[TCPChannel] = []
        self._tasks: dict[asyncio.Task, TCPChannel] = {}

    def _start_channel(self, channel: TCPChannel) -> None:
        """
        Создает и регистрирует задачу обслуживания TCP-канала.
        """
        task = asyncio.create_task(
            channel.start(),
            name=f"channel-{channel.channel_type}",
        )
        self._tasks[task] = channel

    async def start(self) -> None:
        """
        Запускает приложение и создает задачи обслуживания
        для всех сконфигурированных TCP-каналов.
        """
        logger.info("Starting application runtime")

        self._channels = self._builder.build_app()

        for channel in self._channels:
            self._start_channel(channel)

        logger.info(
            "Started {} TCP channel(s)",
            len(self._channels),
        )

    async def wait(self) -> None:
        """
        Непрерывно наблюдает за каналами и автоматически
        перезапускает их при неожиданном завершении.
        """
        while self._tasks:
            done, _ = await asyncio.wait(
                self._tasks.keys(),
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in done:
                channel = self._tasks.pop(task)

                try:
                    task.result()

                    logger.warning(
                        "TCP channel '{}' stopped, restarting",
                        channel.channel_type,
                    )

                except asyncio.CancelledError:
                    logger.info(
                        "TCP channel '{}' cancelled",
                        channel.channel_type,
                    )
                    continue

                except Exception:
                    logger.exception(
                        "TCP channel '{}' crashed, restarting",
                        channel.channel_type,
                    )

                self._start_channel(channel)

    async def shutdown(self) -> None:
        """
        Корректно завершает работу всех TCP-каналов.
        """
        logger.info("Stopping application runtime")

        for task in self._tasks:
            task.cancel()

        await asyncio.gather(
            *self._tasks,
            return_exceptions=True,
        )

        for channel in self._channels:
            await channel.stop()

        self._tasks.clear()

        logger.info("Application runtime stopped")