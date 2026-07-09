import asyncio
from bootstrap import AppBuilder


async def main():
    channels = AppBuilder.build_app()
    tasks = [
        asyncio.create_task(channel.start())
        for channel in channels
    ]
    try:
        await asyncio.Event().wait()
    finally:
        for channel in channels:
            await channel.stop()
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(main())
