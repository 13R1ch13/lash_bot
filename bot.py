from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, REDIS_HOST, REDIS_PORT, REDIS_DB
import redis
import logging

bot = Bot(token=BOT_TOKEN)
redis_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

try:
    redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB).ping()
    storage = RedisStorage.from_url(redis_url)
except redis.exceptions.ConnectionError:
    logging.warning("Redis unavailable, using in-memory storage")
    storage = MemoryStorage()

dp = Dispatcher(storage=storage)
