import asyncio
from core.infrastructure.network.tcp.exception import SessionRemoteClose
from core.infrastructure.network.tcp.session import TCPSession
from core.application.sessions.managed_sessions import ManagedSession
from core.application.sessions.session_registry import SessionRegistry


class SessionManager:
    def __init__(self, registry: SessionRegistry) -> None:
        self._registry = registry
        self._lock = asyncio.Lock()


    async def on_connect(self, session: TCPSession):
        managed = ManagedSession(session=session)
        await self._registry.add(managed)
        task = asyncio.create_task(self._run(managed))
        managed.task = task

    #Вот эту задачу мы храним в Regiser в task
    async def _run(self, managed: ManagedSession) -> None:
        try:
            await managed.session.run()
        except SessionRemoteClose:
            pass
        except asyncio.CancelledError:
            pass
        except Exception:
            raise
        finally:
            await self._registry.delete(managed)


    async def shutdown(self) -> None:
        async with self._lock:
            sessions = await self._registry.all()
            tasks = [s.task for s in sessions if s.task]#Забираю все задачи по сессиям
        for t in tasks:
            t.cancel()#Всем закидываю asyncio.CancelledError