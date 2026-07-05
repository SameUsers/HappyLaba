import asyncio

from core.application import SessionManager
from core.infrastructure.network.tcp.session import TCPSession
from core.config.tcp import TCPServerCongig, TCPSessionConfig


class TCPServer:
    def __init__(
        self,
        session_manager: SessionManager,
        server_config: TCPServerCongig,
        session_config: TCPSessionConfig
    ) -> None:
        self._server: asyncio.Server | None = None
        self._config = server_config
        self._session_config = session_config
        self._session_manager = session_manager


    async def _handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        session = TCPSession(
            reader=reader,
            writer=writer,
            config=self._session_config
        )
        self._session_manager.on_connect(session)
        await self._session_manager.manage(session)


    async def start(self) -> None:
        if self._server is not None:
            raise RuntimeError("Server already running.")

        self._server = await asyncio.start_server(
            self._handle_connection,
            host=self.host,
            port=self.port,
        )
        await self._server.serve_forever()


    async def stop(self) -> None:
        if self._server is None:
            return
        # TODO: graceful shutdown of active sessions
        self._server.close()
        await self._server.wait_closed()
        self._server = None


    @property
    def host(self)->str:
        return self._config.host


    @property
    def port(self)->int:
        return self._config.port

    
    @property
    def session_manager(self)->SessionManager:
        return self._session_manager
    