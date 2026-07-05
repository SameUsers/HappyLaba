import asyncio

from loguru import logger

from core.infrastructure.network.tcp.exception import SessionRemoteClose
from core.infrastructure.network.tcp.session import TCPSession
from core.application.sessions.managed_sessions import ManagedSession
from core.application.sessions.session_registry import SessionRegistry


class SessionManager:
    def __init__(self, registry: SessionRegistry) -> None:
        self._registry = registry
        self._lock = asyncio.Lock()

        logger.debug("SessionManager initialized")

    async def on_connect(self, session: TCPSession) -> None:
        logger.info(
            "New session accepted from {}:{}",
            session.host,
            session.port,
        )

        managed = ManagedSession(session=session)

        await self._registry.add(managed)

        logger.debug(
            "Managed session {} registered",
            managed.id,
        )

        task = asyncio.create_task(self._run(managed))
        managed.task = task

        logger.debug(
            "Background task created for session {}",
            managed.id,
        )

    async def _run(self, managed: ManagedSession) -> None:
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

            await self._registry.delete(managed)

            logger.debug(
                "Session {} cleanup completed",
                managed.id,
            )

    async def shutdown(self) -> None:
        logger.info("Session manager shutdown started")

        async with self._lock:
            sessions = await self._registry.all()
            tasks = [s.task for s in sessions if s.task]

        logger.info(
            "Cancelling {} active session(s)",
            len(tasks),
        )

        for task in tasks:
            task.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info("All session tasks have been stopped")

    def __del__(self) -> None:
        logger.warning("SessionManager object destroyed")