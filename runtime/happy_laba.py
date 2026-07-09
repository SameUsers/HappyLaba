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

    async def start(self) -> None:
        logger.info("Starting HappyLaba runtime")

        self._channels = self._builder.build_app()

        for channel in self._channels:
            task = asyncio.create_task(
                channel.start(),
                name=f"channel-{channel.channel_type}",
            )
            self._tasks[task] = channel
        logger.info(
            "Started {} TCP channel(s)",
            len(self._channels),
        )

    async def wait(self) -> None:
        """
        Непрерывно наблюдает за каналами и перезапускает их
        при неожиданном завершении.
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
                        "TCP channel '{}' stopped. Restarting...",
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
                        "TCP channel '{}' crashed. Restarting...",
                        channel.channel_type,
                    )

                new_task = asyncio.create_task(
                    channel.start(),
                    name=f"channel-{channel.channel_type}",
                )

                self._tasks[new_task] = channel

    async def shutdown(self) -> None:
        """
        Корректно завершает работу всех каналов.
        """

        logger.info("Shutting down HappyLaba runtime")
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(
            *self._tasks,
            return_exceptions=True,
        )
        for channel in self._channels:
            await channel.stop()
        self._tasks.clear()
        logger.info("HappyLaba runtime stopped")