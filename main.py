import asyncio

from runtime.happy_laba import HappyLaba


async def main() -> None:
    """
    Точка входа в приложение.

    Запускает среду выполнения приложения и ожидает
    завершения ее работы.
    """
    app = HappyLaba()

    try:
        await app.start()
        await app.wait()
    finally:
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())