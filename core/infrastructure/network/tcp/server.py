import asyncio

from loguru import logger

from core.application.sessions.factories.session_factory import SessionFactory
from core.application.sessions.session_manager import SessionManager
from core.config.tcp import TCPServerConfig, TCPSessionConfig


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
        session_manager: SessionManager,
        server_config: TCPServerConfig,
        session_config: TCPSessionConfig,
    ) -> None:
        """
        Инициализирует TCP-сервер.

        Args:
            session_manager:
                Менеджер, отвечающий за жизненный цикл активных сессий.

            server_config:
                Конфигурация сетевого сервера.

            session_config:
                Конфигурация создаваемых TCP-сессий.
        """
        self._server: asyncio.Server | None = None
        self._config = server_config
        self._session_config = session_config
        self._session_manager = session_manager
        self._lock = asyncio.Lock()

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
        """
        Обрабатывает новое входящее TCP-подключение.

        Создает объект TCP-сессии через фабрику и передает
        его SessionManager для дальнейшего управления жизненным циклом.

        Args:
            reader:
                Поток чтения данных клиента.

            writer:
                Поток записи данных клиенту.
        """
        session = SessionFactory.create_session(
            reader=reader,
            writer=writer,
            config=self._session_config,
        )

        logger.info(
            "Session created for peer {}:{}",
            session.host,
            session.port,
        )

        self._session_manager.on_connect(session)

    async def start(self) -> None:
        """
        Запускает TCP-сервер и начинает прием клиентских подключений.

        Создает asyncio TCP server, привязывает обработчик новых
        соединений и запускает цикл обслуживания подключений.

        Raises:
            RuntimeError:
                Если сервер уже был запущен.
        """
        async with self._lock:
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
        """
        Выполняет корректное завершение TCP-сервера.

        Прекращает прием новых подключений, ожидает закрытия
        серверного сокета и инициирует остановку всех активных сессий.

        Если сервер уже остановлен, метод завершает работу без ошибки.
        """
        async with self._lock:
            if self._server is None:
                logger.warning(
                    "Stop called but server is not running"
                )
                return

            logger.info(
                "Shutdown requested for TCP server"
            )

            server = self._server
            self._server = None

            server.close()

        logger.debug(
            "Server socket closed, stopping accept loop"
        )

        wait_task = asyncio.create_task(server.wait_closed()
        )

        shutdown_task = asyncio.create_task(
            self._session_manager.shutdown()
        )

        logger.debug(
            "Waiting for server and session manager shutdown"
        )

        await wait_task
        await shutdown_task

        logger.info(
            "TCP server shutdown completed"
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