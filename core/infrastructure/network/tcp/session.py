import asyncio

from core.common.generate_id import generate_uuid
from core.config.tcp import TCPSessionConfig
from core.infrastructure.network.tcp.exception import (
    InvalidPeerInfo,
    SessionRemoteClose,
)


class TCPSession:
    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        config: TCPSessionConfig,
    ) -> None:
        self._id = generate_uuid()
        self._reader = reader
        self._writer = writer
        self._read_size = config.read_size

        peer = self._writer.get_extra_info("peername")
        if peer is None:
            raise InvalidPeerInfo("Remote peer information is unavailable.")

        self._host, self._port = peer


    async def run(self) -> None:
        try:
            await self._receive_loop()
        finally:
            await self._close()


    async def _receive_loop(self) -> None:
        try:
            while True:
                chunk = await self._reader.read(self.read_size)
                if not chunk:
                    raise self._remote_close_error()
                # TODO: Framer.feed(chunk)

        except asyncio.CancelledError:
            raise

        except ConnectionResetError as exc:
            raise self._remote_close_error() from exc


    async def _close(self) -> None:
        if self._writer.is_closing():
            return
        self._writer.close()
        await self._writer.wait_closed()


    def _remote_close_error(self) -> SessionRemoteClose:
        return SessionRemoteClose(
            f"Session '{self.id}' was closed by remote peer."
        )


    @property
    def id(self) -> str:
        return self._id


    @property
    def host(self) -> str:
        return self._host


    @property
    def port(self) -> int:
        return self._port


    @property
    def read_size(self) -> int:
        return self._read_size
