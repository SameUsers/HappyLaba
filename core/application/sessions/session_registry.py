from core.application.sessions.managed_sessions import ManagedSession
import asyncio

class SessionRegistry:
    def __init__(self) -> None:
        self._storage: dict[str, ManagedSession] = {}
        self._lock = asyncio.Lock()


    async def add(self, managed_session: ManagedSession) -> None:
        async with self._lock:
            if managed_session.id in self._storage:
                raise ValueError(f"Session '{managed_session.id}' already registered.")
            self._storage[managed_session.id] = managed_session


    async def delete(self, managed_session: ManagedSession) -> None:
        async with self._lock:
            if managed_session.id in self._storage:
                self._storage.pop(managed_session.id)


    async def get(self, session_id: str) -> ManagedSession:
        async with self._lock:
            session = self._storage.get(session_id)
            if session is None:
                raise KeyError(f"Session '{session_id}' not found.")
            return session


    async def all(self) -> list[ManagedSession]:
        async with self._lock:
            return list(self._storage.values())