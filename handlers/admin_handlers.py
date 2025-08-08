from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from config import ADMIN_IDS
from db.database import get_service_counts
from services.services import services

router = Router()

@router.message(Command("stats"))
async def stats(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    parts = message.text.split()
    start_date = end_date = None
    if len(parts) == 3:
        start_date, end_date = parts[1], parts[2]

    counts = get_service_counts(start_date, end_date)
    if not counts:
        await message.answer("Записей не найдено.")
        return

    total_minutes = 0
    lines = []
    for service, count in counts:
        lines.append(f"{service}: {count}")
        total_minutes += count * services.get(service, 0)

    header = "Общая статистика:" if not start_date else f"Статистика с {start_date} по {end_date}:"
    text = "\n".join(lines)
    hours = total_minutes / 60
    text += f"\n\nВсего часов: {hours:.1f}"
    await message.answer(f"{header}\n{text}")
