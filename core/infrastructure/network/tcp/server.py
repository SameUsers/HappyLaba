import asyncio

from loguru import logger

from core.application.sessions.factories.session_factory import SessionFactory
from core.application.sessions.session_manager import SessionManager
from core.config.tcp import DeviceChannelConfig, DeviceSessionConfig


class TCPChannel:
    """
    Принимает входящие TCP-соединения и передает управление
    созданными сессиями менеджеру сессий.

    Ответственность:
    - запуск и остановка TCP-канала;
    - прием новых клиентских подключений;
    - создание объектов TCP-сессий через фабрику;
    - передача созданных сессий в SessionManager;
    - координация завершения сетевого слоя.

    TCPChannel отвечает только за транспортный уровень и не управляет
    жизненным циклом отдельных сессий.
    """

    def __init__(
        self,
        channel_type: str,
        session_manager: SessionManager,
        server_config: DeviceChannelConfig,
        session_config: DeviceSessionConfig,
    ) -> None:
        """
        Инициализирует TCP-канал.

        Args:
            session_manager:
                Менеджер жизненного цикла активных сессий.

            server_config:
                Конфигурация TCP-канала.

            session_config:
                Конфигурация создаваемых TCP-сессий.
        """
        self._channel_type = channel_type
        self._server: asyncio.Server | None = None
        self._config = server_config
        self._session_config = session_config
        self._session_manager = session_manager
        self._lock = asyncio.Lock()

        logger.debug(
            "TCP channel '{}' initialized on {}:{}",
            self._channel_type,
            self.host,
            self.port,
        )

    async def _create_server(self) -> None:
        """
        Создает и привязывает TCP-сервер к сокету.
        """
        try:
            self._server = await asyncio.start_server(
                self._handle_connection,
                host=self.host,
                port=self.port,
            )
        except OSError:
            logger.exception(
                "Failed to start TCP channel '{}' on {}:{}",
                self._channel_type,
                self.host,
                self.port,
            )
            raise

    async def _close_server(self, server: asyncio.Server) -> None:
        """
        Выполняет корректное завершение TCP-сервера.
        """
        server.close()

        logger.debug(
            "Closing TCP channel '{}'",
            self._channel_type,
        )

        await asyncio.gather(
            server.wait_closed(),
            self._session_manager.shutdown(channel_type=self._channel_type),
        )

    def _handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """
        Обрабатывает новое входящее TCP-подключение.

        Создает TCP-сессию через фабрику и передает
        ее менеджеру сессий.
        """
        session = SessionFactory.create_session(
            reader=reader,
            writer=writer,
            config=self._session_config,
        )

        logger.info(
            "Accepted connection on TCP channel '{}' from {}:{}",
            self._channel_type,
            session.host,
            session.port,
        )

        self._session_manager.on_connect(session, self._channel_type)

    async def start(self) -> None:
        """
        Запускает TCP-канал и начинает прием клиентских подключений.
        """
        async with self._lock:
            if self._server is not None:
                raise RuntimeError("TCP channel already running.")

            await self._create_server()

        logger.info(
            "TCP channel '{}' started on {}:{}",
            self._channel_type,
            self.host,
            self.port,
        )

        try:
            await self._server.serve_forever()

        except asyncio.CancelledError:
            logger.debug(
                "TCP channel '{}' task cancelled",
                self._channel_type,
            )
            raise
        except Exception:
            logger.exception(
                "TCP channel '{}' stopped unexpectedly",
                self._channel_type,
            )
            raise

    async def stop(self) -> None:
        """
        Выполняет корректное завершение TCP-канала.

        Прекращает прием новых подключений и завершает
        связанные сессии.
        """
        async with self._lock:
            if self._server is None:
                logger.warning(
                    "Shutdown requested for TCP channel '{}' but it is not running",
                    self._channel_type,
                )
                return

            logger.info(
                "Stopping TCP channel '{}'",
                self._channel_type,
            )

            server = self._server
            self._server = None

        await self._close_server(server)

        logger.info(
            "TCP channel '{}' stopped",
            self._channel_type,
        )

    @property
    def host(self) -> str:
        return self._config.host

    @property
    def port(self) -> int:
        return self._config.port

    @property
    def channel_type(self) -> str:
        return self._channel_type

    @property
    def session_manager(self) -> SessionManager:
        return self._session_manager