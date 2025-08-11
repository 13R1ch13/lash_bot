from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from config import BOT_TOKEN, REDIS_HOST, REDIS_PORT, REDIS_DB

bot = Bot(token=BOT_TOKEN)
redis_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
storage = RedisStorage.from_url(redis_url)
dp = Dispatcher(storage=storage)
