import pytest
from core.application.sessions.session_registry import SessionRegistry
from core.application.sessions.managed_sessions import ManagedSession
from tests.application.fake.fake_tcp_session import FakeTCPSession

@pytest.fixture
def session_registry()->SessionRegistry:
    """
    Фикстура для возврата обьекта класса SessionRegistry
    """
    return SessionRegistry()

@pytest.fixture
def fake_tcp_session()->FakeTCPSession:
    return FakeTCPSession()

@pytest.fixture
def fake_session_context(fake_tcp_session)->ManagedSession:
    return ManagedSession(session=fake_tcp_session)
