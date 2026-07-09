import asyncio

from loguru import logger

from core.application.sessions.factories.session_factory import SessionFactory
from core.application.sessions.session_manager import SessionManager
from core.config.tcp import DeviceChannelConfig, DeviceSessionConfig


class TCPServer:
    """
    Принимает входящие TCP-соединения и передает управление
    созданными сессиями менеджеру сессий.

    Ответственность:
    - запуск и остановка TCP-сервера;
    - прием новых клиентских подключений;
    - создание объектов TCP-сессий через фабрику;
    - передача созданных сессий в SessionManager;
    - координация завершения сетевого слоя.

    TCPServer отвечает за транспортный уровень и не управляет
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
        Инициализирует TCP-сервер.

        Args:
            session_manager:
                Менеджер, отвечающий за жизненный цикл активных сессий.

            server_config:
                Конфигурация TCP-канала устройства.

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
            self._config.host,
            self._config.port,
        )

    async def _handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """
        Обрабатывает новое входящее TCP-подключение.

        Создает объект TCP-сессии через фабрику и передает
        его SessionManager для дальнейшего управления жизненным циклом.
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
            try:
                self._server = await asyncio.start_server(
                    self._handle_connection,
                    host=self.host,
                    port=self.port,
                )
            except OSError as exc:
                logger.error(
                    "Failed to start TCP channel '{}' on {}:{} - {}",
                    self._channel_type,
                    self.host,
                    self.port,
                    exc,
                )
                raise

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
        except Exception as exc:
            logger.error(
                "TCP channel '{}' stopped unexpectedly: {}",
                self._channel_type,
                exc,
            )
            raise

    async def stop(self) -> None:
        """
        Выполняет корректное завершение TCP-канала.

        Прекращает прием новых подключений и завершает
        активные сессии через SessionManager.
        """
        async with self._lock:
            if self._server is None:
                logger.warning(
                    "Shutdown requested for TCP channel '{}' but it is not running",
                    self._channel_type,
                )
                return
            logger.info(
                "Shutdown requested for TCP channel '{}'",
                self._channel_type,
            )
            server = self._server
            self._server = None
            server.close()
        logger.debug(
            "TCP channel '{}' socket closed, stopping accept loop",
            self._channel_type,
        )
        wait_task = asyncio.create_task(server.wait_closed())
        shutdown_task = asyncio.create_task(
            self._session_manager.shutdown(channel_type=self._channel_type)
        )
        logger.debug(
            "Waiting for TCP channel '{}' and session manager shutdown",
            self._channel_type,
        )
        await wait_task
        await shutdown_task
        logger.info(
            "TCP channel '{}' shutdown completed",
            self._channel_type,
        )

    @property
    def host(self) -> str:
        return self._config.host

    @property
    def port(self) -> int:
        return self._config.port

    @property
    def session_manager(self) -> SessionManager:
        return self._session_manager
