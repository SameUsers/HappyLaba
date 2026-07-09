from functools import lru_cache

from loguru import logger

from core.config import load_config
from core.infrastructure.network.tcp.server import TCPServer
from core.application.sessions.session_manager import SessionManager
from core.application.sessions.session_registry import SessionRegistry


class AppBuilder:

    @staticmethod
    @lru_cache(maxsize=1)
    def _create_session_manager() -> SessionManager:
        logger.debug("Creating session registry")

        app_session_registry = SessionRegistry()

        logger.debug("Creating session manager")

        return SessionManager(
            registry=app_session_registry,
        )

    @staticmethod
    def build_app() -> list[TCPServer]:
        logger.info("Starting application initialization")

        logger.debug("Loading application configuration")

        app_config = load_config()

        app_session_manager = AppBuilder._create_session_manager()

        channels: list[TCPServer] = []
        ports: set[int] = set()

        for device_config in app_config.devices_config:
            port = device_config.device_channel.port
            host = device_config.device_channel.host

            logger.debug(
                "Creating TCP channel for device type '{}' on {}:{}",
                device_config.device_type,
                host,
                port,
            )

            if port in ports:
                raise RuntimeError(
                    f"Port {port} already configured for another device"
                )

            ports.add(port)

            server = TCPServer(
                channel_type=device_config.device_type,
                server_config=device_config.device_channel,
                session_config=device_config.device_session,
                session_manager=app_session_manager,
            )

            logger.info(
                "TCP channel configured for device '{}' on {}:{}",
                device_config.device_type,
                host,
                port,
            )

            channels.append(server)

        logger.info(
            "Application initialized successfully. Configured TCP channels: {}",
            len(channels),
        )

        return channels