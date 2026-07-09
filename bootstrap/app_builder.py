from functools import lru_cache

from loguru import logger

from core.application.sessions.session_manager import SessionManager
from core.application.sessions.session_registry import SessionRegistry
from core.common.awailable_port import port_available
from core.config import load_config
from core.config.config import DeviceConfig
from core.infrastructure.network.tcp.server import TCPChannel


class AppBuilder:
    """
    Загружает конфигурацию приложения, выполняет её валидацию
    и создает готовые к использованию TCP-каналы.
    """

    def __init__(self) -> None:
        self._used_ports: set[int] = set()

    def _validate_channel(self, channel: DeviceConfig) -> None:
        """
        Выполняет валидацию конфигурации TCP-канала.

        Проверяет:
        - уникальность порта в конфигурации приложения;
        - доступность порта в операционной системе.

        Raises:
            RuntimeError:
                Если порт уже используется в конфигурации или недоступен.
        """
        port = channel.device_channel.port
        host = channel.device_channel.host

        if port in self._used_ports:
            raise RuntimeError(f"Duplicate TCP port configured: {port}")

        self._used_ports.add(port)

        if not port_available(port=port, host=host):
            raise RuntimeError(f"TCP port is unavailable: {host}:{port}")

    @lru_cache(maxsize=1)
    def _create_session_manager(self) -> SessionManager:
        """
        Создает общий менеджер сессий приложения.
        """
        logger.debug("Creating session registry")

        registry = SessionRegistry()

        logger.debug("Creating session manager")

        return SessionManager(registry=registry)

    def build_app(self) -> list[TCPChannel]:
        """
        Создает и инициализирует все TCP-каналы приложения
        на основании конфигурации.

        Returns:
            Список готовых TCP-каналов.
        """
        logger.info("Initializing application")

        logger.debug("Loading application configuration")

        app_config = load_config()
        session_manager = self._create_session_manager()

        channels: list[TCPChannel] = []

        for channel_config in app_config.channel_config:
            self._validate_channel(channel_config)

            host = channel_config.device_channel.host
            port = channel_config.device_channel.port

            logger.debug(
                "Creating TCP channel '{}' on {}:{}",
                channel_config.device_type,
                host,
                port,
            )

            channel = TCPChannel(
                channel_type=channel_config.device_type,
                server_config=channel_config.device_channel,
                session_config=channel_config.device_session,
                session_manager=session_manager,
            )

            logger.info(
                "TCP channel '{}' configured on {}:{}",
                channel_config.device_type,
                host,
                port,
            )

            channels.append(channel)

        logger.info(
            "Application initialized with {} TCP channel(s)",
            len(channels),
        )

        return channels