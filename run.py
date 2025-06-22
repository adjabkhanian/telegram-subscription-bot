import asyncio
import os

from bot import main as bot_main  # запуск aiogram
from admin.app import app

from hypercorn.asyncio import serve
from hypercorn.config import Config

async def main():
    config = Config()
    config.bind = [f"0.0.0.0:{int(os.environ.get('PORT', 5000))}"]

    flask_task = asyncio.create_task(serve(app, config))
    bot_task = asyncio.create_task(bot_main())

    await asyncio.gather(flask_task, bot_task)

if __name__ == "__main__":
    asyncio.run(main())