# main.py
import asyncio
from bot import bot, dp
from handlers import user_handlers, admin_handlers
from db.database import init_db

async def main():
    init_db()  # создаёт базу данных при запуске
    dp.include_router(user_handlers.router)
    dp.include_router(admin_handlers.router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
