from core.config import load_config
from core.infrastructure.network.tcp.server import TCPServer
from core.application.sessions.session_manager import SessionManager
from core.application.sessions.session_registry import SessionRegistry

class AppBuilder:


    @staticmethod
    def build_app()->TCPServer:
        app_config = load_config()
        app_session_registry = SessionRegistry()
        app_session_manager = SessionManager(registry=app_session_registry)
        return TCPServer(
            server_config=app_config.tcp.server,
            session_config=app_config.tcp.session,
            session_manager=app_session_manager,
        )
