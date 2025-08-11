from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from config import ADMIN_IDS
from bot import bot
from db.user_storage import get_all_users
import logging
from db.database import get_service_counts
from services.services import services
from states.admin import AdminStates

router = Router()


async def build_stats_text(start_date: str | None = None, end_date: str | None = None) -> str:
    counts = await get_service_counts(start_date, end_date)
    if not counts:
        return "Записей не найдено."

    total_minutes = 0
    lines = []
    for service, count in counts:
        lines.append(f"{service}: {count}")
        total_minutes += count * services.get(service, 0)

    header = "Общая статистика:" if not start_date else f"Статистика с {start_date} по {end_date}:"
    text = "\n".join(lines)
    hours = total_minutes / 60
    text += f"\n\nВсего часов: {hours:.1f}"
    return f"{header}\n{text}"


@router.message(Command("stats"))
async def stats(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    parts = message.text.split()
    start_date = end_date = None
    if len(parts) == 3:
        start_date, end_date = parts[1], parts[2]

    await message.answer(await build_stats_text(start_date, end_date))


@router.message(F.text == "📊 Статистика")
async def stats_prompt(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer(
        "Введите диапазон дат в формате YYYY-MM-DD YYYY-MM-DD или '-' для всей статистики"
    )
    await state.set_state(AdminStates.stats_range)


@router.message(AdminStates.stats_range)
async def stats_range(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await state.clear()
        return

    text = message.text.strip()
    start_date = end_date = None
    if text != "-":
        parts = text.split()
        if len(parts) != 2:
            await message.answer(
                "Введите две даты через пробел в формате YYYY-MM-DD YYYY-MM-DD или '-'"
            )
            return
        start_date, end_date = parts

    await message.answer(await build_stats_text(start_date, end_date))
    await state.clear()

@router.message(Command("broadcast"))
async def broadcast(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /broadcast <message>")
        return
    text = parts[1]
    user_ids = get_all_users()
    for user_id in user_ids:
        try:
            await bot.send_message(user_id, text)
        except Exception as e:
            logging.exception(f"Failed to send broadcast to {user_id}: {e}")
    await message.answer("Рассылка завершена.")
