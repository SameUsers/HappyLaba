from loguru import logger

from core.config import load_config
from core.infrastructure.network.tcp.server import TCPServer
from core.application.sessions.session_manager import SessionManager
from core.application.sessions.session_registry import SessionRegistry


class AppBuilder:

    @staticmethod
    def build_app() -> TCPServer:
        logger.info("Starting application initialization")

        logger.debug("Loading application configuration")
        app_config = load_config()

        logger.debug("Creating session registry")
        app_session_registry = SessionRegistry()

        logger.debug("Creating session manager")
        app_session_manager = SessionManager(
            registry=app_session_registry,
        )

        logger.debug("Creating TCP server")
        server = TCPServer(
            server_config=app_config.tcp.server,
            session_config=app_config.tcp.session,
            session_manager=app_session_manager,
        )
        
        logger.info(
            "Application initialized successfully. TCP server configured for {}:{}",
            app_config.tcp.server.host,
            app_config.tcp.server.port,
        )

        return server