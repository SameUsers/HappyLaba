import asyncio

from loguru import logger

from core.application.sessions.managed_sessions import ManagedSession


class SessionRegistry:
    def __init__(self) -> None:
        self._storage: dict[str, ManagedSession] = {}
        self._lock = asyncio.Lock()

        logger.debug("SessionRegistry initialized")

    async def add(self, managed_session: ManagedSession) -> None:
        async with self._lock:
            if managed_session.id in self._storage:
                logger.error(
                    "Attempt to register duplicate session {}",
                    managed_session.id,
                )
                raise ValueError(
                    f"Session '{managed_session.id}' already registered."
                )

            self._storage[managed_session.id] = managed_session

            logger.info(
                "Session {} registered. Active sessions: {}",
                managed_session.id,
                len(self._storage),
            )

    async def delete(self, managed_session: ManagedSession) -> None:
        async with self._lock:
            if managed_session.id not in self._storage:
                logger.warning(
                    "Attempt to remove unknown session {}",
                    managed_session.id,
                )
                return

            self._storage.pop(managed_session.id)

            logger.info(
                "Session {} removed. Active sessions: {}",
                managed_session.id,
                len(self._storage),
            )

    async def get(self, session_id: str) -> ManagedSession:
        async with self._lock:
            session = self._storage.get(session_id)

            if session is None:
                logger.error(
                    "Session {} was not found in registry",
                    session_id,
                )
                raise KeyError(
                    f"Session '{session_id}' not found."
                )

            logger.debug(
                "Session {} retrieved from registry",
                session_id,
            )

            return session

    async def all(self) -> list[ManagedSession]:
        async with self._lock:
            logger.debug(
                "Registry snapshot requested. Active sessions: {}",
                len(self._storage),
            )

            return list(self._storage.values())
    
    def __del__(self) -> None:
        logger.warning("SessionRegistry object destroyed")