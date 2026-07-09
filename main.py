import asyncio

from bootstrap import AppBuilder


async def main():
    channels = AppBuilder.build_app()
    tasks = [
        asyncio.create_task(
            channel.start(),
            name=f"tcp-channel-{channel.port}",
        )
        for channel in channels
    ]
    try:
        done, _ = await asyncio.wait(
            tasks,
            return_when=asyncio.FIRST_EXCEPTION,
        )
        for task in done:
            exception = task.exception()
            if exception:
                raise exception
        await asyncio.Event().wait()
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )
        for channel in channels:
            await channel.stop()


if __name__ == "__main__":
    asyncio.run(main())