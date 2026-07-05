import asyncio
from bootstrap import AppBuilder


async def close(server):
    r = await asyncio.to_thread(input, 'Close type: ')
    await server.stop()

async def main():
    server = AppBuilder.build_app()

    asyncio.create_task(server.start())
    await close(server)  # просто ждём ввод


if __name__ == "__main__":
    asyncio.run(main())