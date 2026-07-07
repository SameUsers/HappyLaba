from loguru import logger

from core.application.sessions.managed_sessions import ManagedSession


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
        self._storage: dict[str, ManagedSession] = {}
        logger.debug("SessionRegistry initialized")

    def add(self, managed_session: ManagedSession) -> None:
        """
        Регистрирует новую управляемую сессию.

        Args:
            managed_session:
                Объект сессии, который необходимо добавить в реестр.

        Raises:
            ValueError:
                Если сессия с таким идентификатором уже зарегистрирована.
        """
        if managed_session.id in self._storage:
            logger.error(
                "Attempt to register duplicate session {}",
                managed_session.id,
            )
            raise ValueError(
                f"Session '{managed_session.id}' already registered."
            )
        self._storage[managed_session.id] = managed_session
        logger.info(
            "Session {} registered. Active sessions: {}",
            managed_session.id,
            len(self._storage),
        )

    def delete(self, managed_session: ManagedSession) -> None:
        """
        Удаляет управляемую сессию из реестра.

        Если сессия отсутствует в реестре, операция завершается
        без ошибки.

        Args:
            managed_session:
                Объект сессии, который необходимо удалить.
        """
        if managed_session.id not in self._storage:
            logger.warning(
                "Attempt to remove unknown session {}",
                managed_session.id,
            )
            return

        self._storage.pop(managed_session.id)
        logger.info(
            "Session {} removed. Active sessions: {}",
            managed_session.id,
            len(self._storage),
        )

    def get(self, session_id: str) -> ManagedSession:
        """
        Возвращает активную сессию по идентификатору.

        Args:
            session_id:
                Уникальный идентификатор сессии.

        Returns:
            Найденный объект управляемой сессии.

        Raises:
            KeyError:
                Если сессия с указанным идентификатором отсутствует
                в реестре.
        """
        session = self._storage.get(session_id)
        if session is None:
            logger.error(
                "Session {} was not found in registry",
                session_id,
            )
            raise KeyError(
                f"Session '{session_id}' not found."
            )

        logger.debug(
            "Session {} retrieved from registry",
            session_id,
        )
        return session

    def all(self) -> list[ManagedSession]:
        """
        Возвращает список всех зарегистрированных сессий.

        Returns:
            Список активных управляемых сессий.
        """
        logger.debug(
            "Registry snapshot requested. Active sessions: {}",
            len(self._storage),
        )
        return list(self._storage.values())
