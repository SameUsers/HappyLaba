from loguru import logger

from core.application.sessions.session_context import SessionContext


class SessionRegistry:
    """
    Хранит информацию об активных управляемых сессиях.

    Ответственность:
    - регистрация новых сессий;
    - удаление завершенных сессий;
    - получение сессии по идентификатору;
    - предоставление списка всех активных сессий.

    Registry является источником текущего состояния активных
    сессий и не управляет их жизненным циклом.
    """

    def __init__(self) -> None:
        """
        Инициализирует пустой реестр активных сессий.
        """
        self._storage: dict[str, SessionContext] = {}

        logger.debug("Session registry initialized")

    def add(self, session: SessionContext) -> None:
        """
        Регистрирует новую управляемую сессию.

        Args:
            session:
                Контекст сессии.

        Raises:
            ValueError:
                Если сессия с таким идентификатором уже существует.
        """
        if session.id in self._storage:
            logger.error(
                "Session '{}' is already registered",
                session.id,
            )
            raise ValueError(f"Session '{session.id}' already registered.")

        self._storage[session.id] = session

        logger.info(
            "Registered session '{}', active sessions: {}",
            session.id,
            len(self._storage),
        )

    def delete(self, session: SessionContext) -> None:
        """
        Удаляет управляемую сессию из реестра.

        Если сессия отсутствует в реестре, операция завершается
        без ошибки.

        Args:
            session:
                Контекст сессии.
        """
        if session.id not in self._storage:
            logger.warning(
                "Attempted to remove unknown session '{}'",
                session.id,
            )
            return

        del self._storage[session.id]

        logger.info(
            "Removed session '{}', active sessions: {}",
            session.id,
            len(self._storage),
        )

    def get(self, session_id: str) -> SessionContext:
        """
        Возвращает активную сессию по идентификатору.

        Args:
            session_id:
                Уникальный идентификатор сессии.

        Returns:
            Контекст найденной сессии.

        Raises:
            KeyError:
                Если сессия отсутствует в реестре.
        """
        session = self._storage.get(session_id)

        if session is None:
            logger.error(
                "Session '{}' not found",
                session_id,
            )
            raise KeyError(f"Session '{session_id}' not found.")

        logger.debug(
            "Retrieved session '{}'",
            session_id,
        )

        return session

    def all(self) -> list[SessionContext]:
        """
        Возвращает список всех зарегистрированных сессий.

        Returns:
            Список активных управляемых сессий.
        """
        logger.debug(
            "Retrieved {} active session(s)",
            len(self._storage),
        )

        return list(self._storage.values())
