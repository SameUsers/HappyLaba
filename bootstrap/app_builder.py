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
    Loads application configuration, validates it and creates ready-to-use
    TCP channels.
    """

    _used_ports: set[int] = set()

    def _validate_channel(self, channel: DeviceConfig) -> None:
        port = channel.device_channel.port
        host = channel.device_channel.host

        if port in self._used_ports:
            raise RuntimeError(f"Duplicate TCP port configured: {port}")

        self._used_ports.add(port)

        if not port_available(port=port, host=host):
            raise RuntimeError(f"TCP port is unavailable: {host}:{port}")

    @lru_cache(maxsize=1)
    def _create_session_manager(self) -> SessionManager:
        logger.debug("Creating session registry")

        registry = SessionRegistry()

        logger.debug("Creating session manager")

        return SessionManager(registry=registry)

    def build_app(self) -> list[TCPChannel]:
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