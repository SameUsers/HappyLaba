import asyncio
from bootstrap import AppBuilder


async def main():
    server = AppBuilder.build_app()
    try:
        await server.start()
    except (KeyboardInterrupt, asyncio.CancelledError):
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
