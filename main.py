from bootstrap import AppBuilder
import asyncio


async def main():
    app_builder = AppBuilder()
    app = app_builder.build_app()
    await app.start()

if __name__ == '__main__':
    asyncio.run(main())