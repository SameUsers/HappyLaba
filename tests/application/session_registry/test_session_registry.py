import pytest
from core.application.sessions.session_registry import SessionRegistry
from core.application.sessions.session_manager import ManagedSession


class TestSessionRegistry:

    def test_add_session_registers_and_can_be_retrieved(
        self,
        session_registry: SessionRegistry,
        fake_session_context: ManagedSession
    ) -> None:

        session_registry.add(fake_session_context)

        assert len(session_registry.all()) == 1
        assert session_registry.get(fake_session_context.id).id == fake_session_context.id
        assert session_registry.get(fake_session_context.id).session == fake_session_context.session


    def test_delete_session_removes_it_from_registry(
        self,
        session_registry: SessionRegistry,
        fake_session_context: ManagedSession
    ) -> None:

        session_registry.add(fake_session_context)
        session_registry.delete(fake_session_context)
        with pytest.raises(KeyError):
            session_registry.get(fake_session_context.id)
        assert len(session_registry.all()) == 0


    def test_adding_duplicate_session_raises_error(
        self,
        session_registry: SessionRegistry,
        fake_session_context: ManagedSession
    ) -> None:

        session_registry.add(fake_session_context)
        with pytest.raises(ValueError):
            session_registry.add(fake_session_context)
        assert len(session_registry.all()) == 1


    def test_deleting_unknown_session_is_safe_noop(
        self,
        session_registry: SessionRegistry,
        fake_session_context: ManagedSession
    ) -> None:

        session_registry.delete(fake_session_context)
        assert len(session_registry.all()) == 0


    def test_registry_remains_consistent_across_multiple_operations(
        self,
        session_registry: SessionRegistry,
        fake_session_context: ManagedSession
    ) -> None:

        session_registry.add(fake_session_context)
        session_registry.delete(fake_session_context)
        session_registry.add(fake_session_context)
        session_registry.delete(fake_session_context)
        session_registry.add(fake_session_context)
        assert session_registry.get(fake_session_context.id).id == fake_session_context.id
        assert session_registry.get(fake_session_context.id).session == fake_session_context.session
        assert len(session_registry.all()) == 1
    