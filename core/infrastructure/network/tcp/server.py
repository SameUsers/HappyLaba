import asyncio
from core.application.sessions.session_manager import SessionManager
from core.config.tcp import TCPServerConfig, TCPSessionConfig
from core.infrastructure.network.tcp.session import TCPSession


class TCPServer:
    def __init__(
        self,
        session_manager: SessionManager,
        server_config: TCPServerConfig,
        session_config: TCPSessionConfig,
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
            config=self._session_config,
        )
        await self._session_manager.on_connect(session)


    async def start(self) -> asyncio.Task|None:
        if self._server is not None:
            raise RuntimeError("Server already running.")
        self._server = await asyncio.start_server(
            self._handle_connection,
            host=self.host,
            port=self.port,
        )
        await self._server.serve_forever()#Это чтобы держать EventLoop открытым

    async def stop(self) -> None:
        if self._server is None:#Проверяю что сервер существует
            return
        self._server = None
        self._server.close()#Инициирую закрытие
        await self._session_manager.shutdown()#Вызываю метод закрытия всех соединений
        await self._server.wait_closed()#Ожидаю завершения


    @property
    def host(self) -> str:
        return self._config.host


    @property
    def port(self) -> int:
        return self._config.port


    @property
    def session_manager(self) -> SessionManager:
        return self._session_manager