from dataclasses import dataclass, field
import asyncio
from core.infrastructure.network.tcp.session import TCPSession
from core.common.generate_id import generate_uuid


@dataclass(slots=True)
class ManagedSession:
    session: TCPSession
    task: asyncio.Task | None = None
    id: str = field(default_factory=generate_uuid)