from loguru import logger

from core.config import load_config
from functools import lru_cache
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
        app_session_manager = SessionManager(
            registry=app_session_registry,
        )
        return app_session_manager

    @staticmethod
    def build_app() -> TCPServer:
        logger.info("Starting application initialization")
        logger.debug("Loading application configuration")
        app_config = load_config()
        app_session_manager = AppBuilder._create_session_manager()
        channels: list[TCPServer] = []
        for device_config in app_config.devices_config:
            logger.debug("Creating TCP server for")
            server = TCPServer(
                channel_type=device_config.device_type,
                server_config=device_config.device_channel,
                session_config=device_config.device_session,
                session_manager=app_session_manager,
            )
            logger.info(
                "Application initialized successfully. TCP server configured for {}:{}",
                device_config.device_channel.host,
                device_config.device_channel.port,
            )
            channels.append(server)

        return channels
