from core.infrastructure.network.tcp.session import TCPSession


class SessionRegistry:
    def __init__(self) -> None:
        self._storage: dict[str, TCPSession] = {}


    def add(self, session: TCPSession) -> None:
        if session.id in self._storage:
            raise ValueError(
                f"Session '{session.id}' already registered."
            )
        self._storage[session.id] = session


    def delete(self, session: TCPSession) -> None:
        if session.id not in self._storage:
            raise ValueError(
                f"Session '{session.id}' not found."
            )
        del self._storage[session.id]


    def get(self, session_id: str) -> TCPSession:
        if session_id not in self._storage:
            raise ValueError(
                f"Session '{session_id}' not found."
            )
        return self._storage[session_id]
