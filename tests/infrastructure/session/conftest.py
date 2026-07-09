import pytest
from unittest.mock import MagicMock, AsyncMock
from core.infrastructure.network.tcp.session import TCPSession


@pytest.fixture
def session() -> TCPSession:
    reader = AsyncMock()
    framer = MagicMock()

    writer = MagicMock()
    writer.get_extra_info.return_value = ("127.0.0.1", 8000)
    writer.is_closing.return_value = False
    writer.wait_closed = AsyncMock()

    config = MagicMock()
    config.read_size = 4096

    return TCPSession(
        framer=framer,
        reader=reader,
        writer=writer,
        config=config,
    )
