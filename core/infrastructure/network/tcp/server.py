import asyncio
from core.application.sessions.session_manager import SessionManager
from core.config.tcp import TCPServerConfig, TCPSessionConfig
from core.application.sessions.factories.session_factory import SessionFactory
from loguru import logger


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

        logger.debug(
            "TCPServer initialized on {}:{}",
            self._config.host,
            self._config.port,
        )

    async def _handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        session = SessionFactory.create_session(reader=reader,
                                                writer=writer,
                                                config=self._session_config)
        logger.info(
            "Session created for peer {}:{}",
            session.host,
            session.port,
        )
        asyncio.create_task(self._session_manager.on_connect(session))

    async def start(self) -> asyncio.Task | None:
        if self._server is not None:
            raise RuntimeError("Server already running.")
        self._server = await asyncio.start_server(
            self._handle_connection,
            host=self.host,
            port=self.port,
        )
        logger.info(
            "TCP server started on {}:{}",
            self.host,
            self.port,
        )
        await self._server.serve_forever()

    async def stop(self) -> None:
        if self._server is None:
            logger.warning("Stop called but server is not running")
            return
        logger.info("Shutdown requested for TCP server")
        server = self._server
        self._server = None
        server.close()
        logger.debug("Server socket closed, stopping accept loop")
        wait_task = asyncio.create_task(server.wait_closed())
        shutdown_task = asyncio.create_task(self._session_manager.shutdown())
        logger.debug("Waiting for server and session manager shutdown")
        await wait_task
        await shutdown_task
        logger.info("TCP server shutdown completed")

    @property
    def host(self) -> str:
        return self._config.host

    @property
    def port(self) -> int:
        return self._config.port

    @property
    def session_manager(self) -> SessionManager:
        return self._session_manager
