import asyncio

from loguru import logger

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
        self._reader = reader
        self._writer = writer
        self._read_size = config.read_size

        peer = self._writer.get_extra_info("peername")
        if peer is None:
            logger.error("Failed to retrieve remote peer information")
            raise InvalidPeerInfo("Remote peer information is unavailable.")

        self._host, self._port = peer

        logger.debug(
            "TCP session created for {}:{}",
            self.host,
            self.port,
        )

    async def run(self) -> None:
        logger.debug(
            "Session {}:{} started",
            self.host,
            self.port,
        )

        try:
            await self._receive_loop()

        except asyncio.CancelledError:
            logger.debug(
                "Session {}:{} received cancellation request",
                self.host,
                self.port,
            )
            raise

        except SessionRemoteClose:
            logger.debug(
                "Remote peer {}:{} closed the connection",
                self.host,
                self.port,
            )
            raise

        except Exception:
            logger.exception(
                "Unhandled exception in session {}:{}",
                self.host,
                self.port,
            )
            raise
        finally:
            await self._close()

    async def _receive_loop(self) -> None:
        logger.debug(
            "Receive loop started for {}:{}",
            self.host,
            self.port,
        )
        try:
            while True:
                chunk = await self._reader.read(self.read_size)
                if not chunk:
                    raise SessionRemoteClose
                logger.trace(
                    "Received {} bytes from {}:{}",
                    len(chunk),
                    self.host,
                    self.port,
                )

        except asyncio.CancelledError:
            raise
        except ConnectionResetError:
            logger.debug(
                "Connection reset by peer {}:{}",
                self.host,
                self.port,
            )
            raise
        except SessionRemoteClose:
            raise

    async def _close(self) -> None:
        if self._writer.is_closing():
            logger.trace(
                "Session {}:{} is already closing",
                self.host,
                self.port,
            )
            return
        logger.debug(
            "Closing session {}:{}",
            self.host,
            self.port,
        )

        self._writer.close()
        await self._writer.wait_closed()

        logger.info(
            "Session {}:{} closed",
            self.host,
            self.port,
        )

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @property
    def read_size(self) -> int:
        return self._read_size
