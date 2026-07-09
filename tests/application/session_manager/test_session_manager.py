import asyncio
from unittest.mock import (
    AsyncMock,
    MagicMock,
    create_autospec,
    patch,
)

import pytest

from core.application.sessions.managed_sessions import ManagedSession
from core.application.sessions.session_manager import SessionManager
from core.application.sessions.session_registry import SessionRegistry
from core.infrastructure.network.tcp.session import TCPSession
from core.infrastructure.network.tcp.exception import SessionRemoteClose


class TestSessionManager:

    async def test_on_connect(
        self,
        fake_session_manager: SessionManager,
    ) -> None:
        session = create_autospec(TCPSession, instance=True)
        session.host = "127.0.0.1"
        session.port = 8000

        registry = create_autospec(SessionRegistry, instance=True)
        fake_session_manager._registry = registry

        managed = MagicMock(spec=ManagedSession)
        task = MagicMock()

        fake_session_manager._run = AsyncMock()

        def fake_create_task(coro):
            coro.close()
            return task

        with (
            patch(
                "core.application.sessions.session_manager.ManagedSession",
                return_value=managed,
            ) as managed_cls,
            patch(
                "core.application.sessions.session_manager.asyncio.create_task",
                side_effect=fake_create_task,
            ) as create_task,
        ):
            fake_session_manager.on_connect(session, device_type='Urit5160')

        managed_cls.assert_called_once_with(session=session, device_type='Urit5160')
        registry.add.assert_called_once_with(managed)

        fake_session_manager._run.assert_called_once_with(managed)

        create_task.assert_called_once()
        assert managed.task is task

    @pytest.mark.asyncio
    async def test_run(
        self,
        fake_session_manager: SessionManager,
    ) -> None:
        managed = create_autospec(ManagedSession, instance=True)
        session = create_autospec(TCPSession, instance=True)
        registry = create_autospec(SessionRegistry, instance=True)

        managed.session = session
        session.run = AsyncMock()

        fake_session_manager._registry = registry

        await fake_session_manager._run(managed)

        session.run.assert_awaited_once()
        registry.delete.assert_called_once_with(managed)

    @pytest.mark.asyncio
    async def test_run_cleanup_on_cancelled_error(
        self,
        fake_session_manager: SessionManager,
    ) -> None:
        managed = create_autospec(ManagedSession, instance=True)
        session = create_autospec(TCPSession, instance=True)
        registry = create_autospec(SessionRegistry, instance=True)

        managed.session = session
        session.run = AsyncMock(side_effect=asyncio.CancelledError())

        fake_session_manager._registry = registry

        with pytest.raises(asyncio.CancelledError):
            await fake_session_manager._run(managed)

        session.run.assert_awaited_once()
        registry.delete.assert_called_once_with(managed)

    @pytest.mark.asyncio
    async def test_shutdown_cancels_all_tasks(
        self,
        fake_session_manager: SessionManager,
    ) -> None:
        managed1 = MagicMock()
        managed2 = MagicMock()
        managed1.device_type='Urit5160'
        managed2.device_type='Urit5160'

        task1 = MagicMock()
        task2 = MagicMock()

        managed1.task = task1
        managed2.task = task2

        registry = create_autospec(SessionRegistry, instance=True)
        registry.all.return_value = [managed1, managed2]

        fake_session_manager._registry = registry

        with patch(
            "core.application.sessions.session_manager.asyncio.gather",
            new_callable=AsyncMock,
        ) as gather_mock:
            await fake_session_manager.shutdown(device_type='Urit5160')

        registry.all.assert_called_once_with()

        task1.cancel.assert_called_once_with()
        task2.cancel.assert_called_once_with()

        gather_mock.assert_awaited_once_with(
            task1,
            task2,
            return_exceptions=True,
        )

    @pytest.mark.asyncio
    async def test_run_handles_remote_close(
        self,
        fake_session_manager: SessionManager,
    ) -> None:
        managed = create_autospec(ManagedSession, instance=True)
        session = create_autospec(TCPSession, instance=True)
        registry = create_autospec(SessionRegistry, instance=True)

        managed.session = session
        session.run = AsyncMock(side_effect=SessionRemoteClose())

        fake_session_manager._registry = registry

        await fake_session_manager._run(managed)

        session.run.assert_awaited_once()
        registry.delete.assert_called_once_with(managed)

    @pytest.mark.asyncio
    async def test_run_handles_unexpected_exception(
        self,
        fake_session_manager: SessionManager,
    ) -> None:
        managed = create_autospec(ManagedSession, instance=True)
        session = create_autospec(TCPSession, instance=True)
        registry = create_autospec(SessionRegistry, instance=True)
        managed.session = session
        session.run = AsyncMock(side_effect=RuntimeError("boom"))
        fake_session_manager._registry = registry
        await fake_session_manager._run(managed)
        session.run.assert_awaited_once()
        registry.delete.assert_called_once_with(managed)

        @pytest.mark.asyncio
        async def test_shutdown_skips_sessions_without_tasks(
            self,
            fake_session_manager: SessionManager,
        ) -> None:
            managed_with_task = MagicMock()
            managed_without_task = MagicMock()

            task = MagicMock()

            managed_with_task.task = task
            managed_without_task.task = None

            registry = create_autospec(SessionRegistry, instance=True)
            registry.all.return_value = [
                managed_with_task,
                managed_without_task,
            ]

            fake_session_manager._registry = registry

            with patch(
                "core.application.sessions.session_manager.asyncio.gather",
                new_callable=AsyncMock,
            ) as gather_mock:
                await fake_session_manager.shutdown()

            registry.all.assert_called_once_with()

            task.cancel.assert_called_once_with()

            gather_mock.assert_awaited_once_with(
                task,
                return_exceptions=True,
            )
