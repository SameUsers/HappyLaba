import asyncio
from bootstrap import AppBuilder


async def main():
    server = AppBuilder.build_app()
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())