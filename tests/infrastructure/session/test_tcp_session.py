import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.infrastructure.network.tcp.exception import (
    InvalidPeerInfo,
    SessionRemoteClose,
)
from core.infrastructure.network.tcp.session import TCPSession


class TestTCPSession:


    def test_should_initialize_session_with_valid_peer_info(
        self,
        session: TCPSession,
    ) -> None:
        assert session.host == "127.0.0.1"
        assert session.port == 8000
        assert session.read_size == 4096

        session._writer.get_extra_info.assert_called_once_with("peername")


    @pytest.mark.parametrize(
        "peer",
        [
            None,
            "invalid",
            123,
            [],
            {},
        ],
    )
    def test_should_raise_invalid_peer_info_when_peer_info_is_invalid(
        self,
        peer,
    ) -> None:
        reader = AsyncMock()

        writer = MagicMock()
        writer.get_extra_info.return_value = peer

        config = MagicMock()
        config.read_size = 4096

        with pytest.raises(InvalidPeerInfo):
            TCPSession(reader, writer, config)


    @pytest.mark.asyncio
    async def test_should_run_receive_loop_and_close_session(
        self,
        session: TCPSession,
    ) -> None:
        session._receive_loop = AsyncMock()
        session._close = AsyncMock()

        await session.run()

        session._receive_loop.assert_awaited_once()
        session._close.assert_awaited_once()


    @pytest.mark.asyncio
    async def test_should_reraise_cancelled_error_and_close_session(
        self,
        session: TCPSession,
    ) -> None:
        session._receive_loop = AsyncMock(
            side_effect=asyncio.CancelledError()
        )
        session._close = AsyncMock()

        with pytest.raises(asyncio.CancelledError):
            await session.run()

        session._close.assert_awaited_once()


    @pytest.mark.asyncio
    async def test_should_reraise_session_remote_close_and_close_session(
        self,
        session: TCPSession,
    ) -> None:
        session._receive_loop = AsyncMock(
            side_effect=SessionRemoteClose()
        )
        session._close = AsyncMock()

        with pytest.raises(SessionRemoteClose):
            await session.run()

        session._close.assert_awaited_once()


    @pytest.mark.asyncio
    async def test_should_reraise_unhandled_exception_and_close_session(
        self,
        session: TCPSession,
    ) -> None:
        session._receive_loop = AsyncMock(
            side_effect=RuntimeError()
        )
        session._close = AsyncMock()

        with pytest.raises(RuntimeError):
            await session.run()

        session._close.assert_awaited_once()


    @pytest.mark.asyncio
    async def test_should_raise_session_remote_close_when_peer_disconnects(
        self,
        session: TCPSession,
    ) -> None:
        session._reader.read = AsyncMock(return_value=b"")

        with pytest.raises(SessionRemoteClose):
            await session._receive_loop()

        session._reader.read.assert_awaited_once_with(session.read_size)


    @pytest.mark.asyncio
    async def test_should_reraise_connection_reset_error(
        self,
        session: TCPSession,
    ) -> None:
        session._reader.read = AsyncMock(
            side_effect=ConnectionResetError()
        )

        with pytest.raises(ConnectionResetError):
            await session._receive_loop()


    @pytest.mark.asyncio
    async def test_should_reraise_cancelled_error_from_receive_loop(
        self,
        session: TCPSession,
    ) -> None:
        session._reader.read = AsyncMock(
            side_effect=asyncio.CancelledError()
        )

        with pytest.raises(asyncio.CancelledError):
            await session._receive_loop()


    @pytest.mark.asyncio
    async def test_should_close_writer_when_connection_is_open(
        self,
        session: TCPSession,
    ) -> None:
        await session._close()

        session._writer.close.assert_called_once()
        session._writer.wait_closed.assert_awaited_once()


    @pytest.mark.asyncio
    async def test_should_not_close_writer_when_connection_is_already_closing(
        self,
        session: TCPSession,
    ) -> None:
        session._writer.is_closing.return_value = True

        await session._close()

        session._writer.close.assert_not_called()
        session._writer.wait_closed.assert_not_called()
