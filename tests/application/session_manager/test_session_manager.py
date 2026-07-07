import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from core.application.sessions.session_manager import SessionManager
from core.application.sessions.session_registry import SessionRegistry
from core.infrastructure.network.tcp.session import TCPSession

class TestSessionManager:

    @pytest.mark.asyncio
    async def test_on_connect(self,
                        fake_session_manager: SessionManager) -> None:
        session = MagicMock(spec=TCPSession)
        session.host = '127.0.0.1'
        session.port = 8000

        registry = MagicMock(spec=SessionRegistry)
        fake_session_manager._registry = registry
        fake_session_manager._run = AsyncMock()

        managed = MagicMock()
        task = MagicMock()

        with (
            patch('core.application.sessions.session_manager.ManagedSession',
            return_value=managed
        ) as managed_cls,
            patch('core.application.sessions.session_manager.asyncio.create_task',
                  return_value=task
        ) as create_task):
            await fake_session_manager.on_connect(session=session)
        managed_cls.assert_called_once_with(session=session)
        create_task.assert_called_once()
        registry.add.assert_called_once_with(managed)
        fake_session_manager._run.assert_called_once_with(managed)
        assert managed.task is task

    