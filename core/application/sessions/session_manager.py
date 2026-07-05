from core.infrastructure.network.tcp.exception import SessionRemoteClose
from core.infrastructure.network.tcp.session import TCPSession
from .session_registry import SessionRegistry


class SessionManager:
    def __init__(self, registry: SessionRegistry) -> None:
        self._registry = registry


    def on_connect(self, session: TCPSession) -> None:
        self._registry.add(session)


    async def manage(self, session: TCPSession) -> None:
        try:
            await session.run()
        except SessionRemoteClose:
            # TODO: logging
            pass
        finally:
            self.on_disconnect(session)


    def on_disconnect(self, session: TCPSession) -> None:
        self._registry.delete(session)
