import asyncio
from dataclasses import dataclass, field

from core.common.generate_id import generate_uuid
from core.domain.devices_types import DevicesTypeEnum
from core.infrastructure.network.tcp.session import TCPSession


@dataclass(slots=True)
class SessionContext:
    """
    Представляет контекст TCP-сессии, управляемой SessionManager.

    Объединяет сетевую сессию, связанную с ней фоновую задачу
    и служебные данные, необходимые для управления жизненным
    циклом активного соединения.

    Attributes:
        channel_type:
            Тип TCP-канала, которому принадлежит сессия.

        session:
            Объект TCP-сессии.

        task:
            Фоновая задача asyncio, выполняющая обработку сессии.
            Может отсутствовать до момента запуска обработки.

        id:
            Уникальный идентификатор управляемой сессии.
    """

    channel_type: DevicesTypeEnum
    session: TCPSession
    task: asyncio.Task | None = None
    id: str = field(default_factory=generate_uuid)