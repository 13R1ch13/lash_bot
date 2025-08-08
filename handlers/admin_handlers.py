from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
import datetime

from config import ADMIN_ID
from db.database import add_vacation, remove_vacation

router = Router()


def admin_only(message: Message) -> bool:
    return message.from_user.id == ADMIN_ID


@router.message(Command("add_vacation"))
async def cmd_add_vacation(message: Message):
    if not admin_only(message):
        return
    try:
        date_str = message.text.split()[1]
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except (IndexError, ValueError):
        await message.answer("Использование: /add_vacation YYYY-MM-DD")
        return
    add_vacation(date_str)
    await message.answer(f"День {date_str} добавлен как выходной")


@router.message(Command("remove_vacation"))
async def cmd_remove_vacation(message: Message):
    if not admin_only(message):
        return
    try:
        date_str = message.text.split()[1]
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except (IndexError, ValueError):
        await message.answer("Использование: /remove_vacation YYYY-MM-DD")
        return
    remove_vacation(date_str)
    await message.answer(f"День {date_str} снова доступен для записи")
