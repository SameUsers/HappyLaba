from core.infrastructure.network.tcp.session import TCPSession
from core.config.tcp import TCPSessionConfig
import asyncio

class SessionFactory:
    """
    Фабрика для создания сессии 
    Мне не нравится если Buffer и Framer будут напрямую создаваться в
    самой сессии. Пусть будут через DI через фабрику.
    У каждой сесси свой отдельный заменяемый обьект фреймера и буфера.
    Создается в server.py
    """

    @staticmethod
    def create_session(reader: asyncio.StreamReader, 
                       writer: asyncio.StreamWriter,
                       config: TCPSessionConfig) -> TCPSession:
        return TCPSession(
            reader=reader,
            writer=writer,
            config=config,

        )