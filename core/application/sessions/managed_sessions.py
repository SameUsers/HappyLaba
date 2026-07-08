from dataclasses import dataclass, field
import asyncio
from core.infrastructure.network.tcp.session import TCPSession
from core.common.generate_id import generate_uuid


@dataclass(slots=True)
class ManagedSession:
    """
    Представляет TCP-сессию, управляемую SessionManager.

    Объединяет объект сетевой сессии и связанную с ней
    фоновую задачу выполнения, позволяя отслеживать полный
    жизненный цикл активного соединения.

    Attributes:
        session:
            Объект TCP-сессии, отвечающий за работу с соединением.

        task:
            Фоновая задача asyncio, выполняющая обработку сессии.
            Может отсутствовать до момента запуска обработки.

        id:
            Уникальный идентификатор управляемой сессии.
    """

    session: TCPSession
    task: asyncio.Task | None = None
    id: str = field(default_factory=generate_uuid)
