import asyncio
from bot import bot, dp
from handlers import user_handlers

async def main():
    dp.include_router(user_handlers.router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
