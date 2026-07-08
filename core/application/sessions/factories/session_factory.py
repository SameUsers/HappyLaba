from core.infrastructure.network.tcp.session import TCPSession
from core.config.tcp import TCPSessionConfig
import asyncio


class SessionFactory:
    """
    Фабрика для создания объектов TCP-сессий.

    Инкапсулирует процесс создания TCPSession и скрывает
    детали инициализации внутренних компонентов сессии.

    Ответственность:
    - создание экземпляров TCP-сессий;
    - передача необходимых зависимостей при создании;
    - предоставление единой точки расширения для изменения
      процесса сборки сессии.

    Фабрика не управляет жизненным циклом созданных сессий
    и не отвечает за их выполнение.
    """

    @staticmethod
    def create_session(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        config: TCPSessionConfig,
    ) -> TCPSession:
        """
        Создает и возвращает новый экземпляр TCP-сессии.
            Args:
                reader:
                    Поток чтения данных TCP-соединения.

                writer:
                    Поток записи данных TCP-соединения.

                config:
                    Конфигурация создаваемой сессии.

            Returns:
                Инициализированный объект TCPSession.
        """
        return TCPSession(
            reader=reader,
            writer=writer,
            config=config,
        )
