import pytest
from core.application.sessions.session_registry import SessionRegistry
from core.application.sessions.session_context import SessionContext
from tests.application.fake.fake_tcp_session import FakeTCPSession
from core.application.sessions.session_manager import SessionManager


@pytest.fixture
def session_registry() -> SessionRegistry:
    """
    Фикстура для возврата обьекта класса SessionRegistry
    """
    return SessionRegistry()


@pytest.fixture
def fake_tcp_session() -> FakeTCPSession:
    return FakeTCPSession()


@pytest.fixture
def fake_session_context(fake_tcp_session) -> SessionContext:
    return SessionContext(session=fake_tcp_session, channel_type='Utir5160')


@pytest.fixture
def fake_session_manager(session_registry) -> SessionManager:
    return SessionManager(registry=session_registry)
