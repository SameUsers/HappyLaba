from dataclasses import dataclass, field
import asyncio
from core.infrastructure.network.tcp.session import TCPSession
from core.common.generate_id import generate_uuid
from loguru import logger

@dataclass(slots=True)
class ManagedSession:
    session: TCPSession
    task: asyncio.Task | None = None
    id: str = field(default_factory=generate_uuid)

    def __del__(self) -> None:
        logger.warning("ManagedSession {} destroyed", self.id)