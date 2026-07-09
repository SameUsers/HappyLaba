import asyncio

from loguru import logger

from core.application.sessions.session_context import SessionContext
from core.application.sessions.session_registry import SessionRegistry
from core.domain.devices_types import DevicesTypeEnum
from core.infrastructure.network.tcp.exception import SessionRemoteClose
from core.infrastructure.network.tcp.session import TCPSession


class SessionManager:
    """
    Управляет жизненным циклом активных TCP-сессий.

    Ответственность:
    - регистрация новых сессий в хранилище;
    - создание и контроль фоновых задач выполнения сессий;
    - удаление завершенных сессий из хранилища;
    - координация корректного завершения всех активных сессий.

    SessionManager управляет сессией после её создания,
    но не отвечает за создание и инициализацию TCP-сессий.
    """

    def __init__(self, registry: SessionRegistry) -> None:
        """
        Инициализирует менеджер сессий.

        Args:
            registry:
                Реестр активных сессий.
        """
        self._registry = registry
        self._lock = asyncio.Lock()

        logger.debug("Session manager initialized")

    def _create_context(
        self,
        session: TCPSession,
        channel_type: DevicesTypeEnum,
    ) -> SessionContext:
        """
        Создает контекст управления TCP-сессией.
        """
        managed = SessionContext(
            session=session,
            channel_type=channel_type,
        )

        managed.task = asyncio.create_task(self._run(managed))

        return managed

    async def _shutdown_tasks(
        self,
        channel_type: DevicesTypeEnum,
    ) -> list[asyncio.Task]:
        """
        Возвращает задачи активных сессий указанного TCP-канала.
        """
        async with self._lock:
            return [
                session.task
                for session in self._registry.all()
                if session.channel_type == channel_type and session.task is not None
            ]

    def on_connect(
        self,
        session: TCPSession,
        channel_type: DevicesTypeEnum,
    ) -> None:
        """
        Регистрирует новую TCP-сессию и запускает управление её жизненным циклом.
        """
        logger.info(
            "Accepted session from {}:{}",
            session.host,
            session.port,
        )

        managed = self._create_context(session, channel_type)

        self._registry.add(managed)

        logger.debug(
            "Registered session {}",
            managed.id,
        )

    async def _run(
        self,
        managed: SessionContext,
    ) -> None:
        """
        Выполняет жизненный цикл зарегистрированной сессии.
        """
        logger.debug(
            "Session {} started",
            managed.id,
        )

        try:
            await managed.session.run(managed.channel_type)

        except SessionRemoteClose:
            logger.info(
                "Session {} closed by remote peer",
                managed.id,
            )

        except asyncio.CancelledError:
            logger.warning(
                "Session {} cancelled",
                managed.id,
            )
            raise

        except Exception:
            logger.exception(
                "Session {} crashed",
                managed.id,
            )

        finally:
            self._registry.delete(managed)

            logger.debug(
                "Removed session {}",
                managed.id,
            )

    async def shutdown(
        self,
        channel_type: DevicesTypeEnum,
    ) -> None:
        """
        Корректно завершает работу всех активных сессий указанного TCP-канала.
        """
        logger.info(
            "Stopping sessions for channel '{}'",
            channel_type,
        )

        tasks = await self._shutdown_tasks(channel_type)

        logger.info(
            "Cancelling {} session(s)",
            len(tasks),
        )

        for task in tasks:
            task.cancel()

        await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )
        logger.info(
            "Stopped sessions for channel '{}'",
            channel_type,
        )
