import asyncio
from bootstrap import AppBuilder


async def close(server):
    r = await asyncio.to_thread(input, 'Close type: ')
    print(f"Received: {r}")
    await server.stop()
    print("Server closed")

async def main():
    server = AppBuilder.build_app()

    asyncio.create_task(server.start())
    await close(server)  # просто ждём ввод


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")