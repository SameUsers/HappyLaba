from runtime.happy_laba import HappyLaba
import asyncio

async def main():
    app = HappyLaba()

    try:
        await app.start()
        await app.wait()
    finally:
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())