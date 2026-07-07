import asyncio

from loguru import logger

from core.infrastructure.network.tcp.exception import SessionRemoteClose
from core.infrastructure.network.tcp.session import TCPSession
from core.application.sessions.managed_sessions import ManagedSession
from core.application.sessions.session_registry import SessionRegistry


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
                Реестр активных сессий, используемый для хранения
                и управления зарегистрированными сессиями.
        """
        self._registry = registry
        self._lock = asyncio.Lock()
        logger.debug("SessionManager initialized")


    async def on_connect(self, session: TCPSession) -> None:
        """
        Регистрирует новую TCP-сессию и запускает управление её жизненным циклом.

        Создает объект ManagedSession, запускает фоновую задачу
        для обработки сессии, сохраняет задачу в объекте ManagedSession
        и добавляет полностью подготовленную сессию в реестр.

        Args:
            session:
                Инициализированный объект TCP-сессии.
        """
        logger.info(
            "New session accepted from {}:{}",
            session.host,
            session.port,
        )

        managed = ManagedSession(session=session)#Тут обьект без задачи
        self._registry.add(managed)
        task = asyncio.create_task(self._run(managed))
        managed.task = task#Тут я ему присваиваю задача

        logger.debug(
            "Managed session {} registered",
            managed.id,
        )

        logger.debug(
            "Background task created for session {}",
            managed.id,
        )


    async def _run(self, managed: ManagedSession) -> None:
        """
        Управляет выполнением жизненного цикла сессии.

        Запускает обработку сессии и гарантирует удаление завершенной
        сессии из реестра независимо от причины завершения.

        Args:
            managed:
                Полностью инициализированный объект управляемой сессии.
        
        Raises:
            asyncio.CancelledError:
                Пробрасывается при отмене задачи во время завершения сервера.
        """
        logger.debug(
            "Session {} processing started",
            managed.id,
        )
        try:
            await managed.session.run()
        except SessionRemoteClose:
            logger.info(
                "Session {} closed by remote peer",
                managed.id,
            )
        except asyncio.CancelledError:
            logger.warning(
                "Session {} cancelled during server shutdown",
                managed.id,
            )
            raise
        except Exception:
            logger.exception(
                "Unhandled exception in session {}",
                managed.id,
            )

        finally:
            logger.debug(
                "Removing session {} from registry",
                managed.id,
            )
            self._registry.delete(managed)
            logger.debug(
                "Session {} cleanup completed",
                managed.id,
            )


    async def shutdown(self) -> None:
        """
        Корректно завершает работу всех активных сессий.

        Получает активные задачи из реестра сессий, отправляет каждой задаче
        сигнал отмены и ожидает полного завершения их работы.

        Отмена распространяется через жизненный цикл сессии и обрабатывается
        соответствующими компонентами.
        """

        logger.info("Session manager shutdown started")

        async with self._lock:
            sessions = self._registry.all()
            tasks = [s.task for s in sessions if s.task]

        logger.info(
            "Cancelling {} active session(s)",
            len(tasks),
        )

        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info("All session tasks have been stopped")
