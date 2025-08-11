from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
from config import ADMIN_IDS
from bot import bot
from db.user_storage import get_all_users
import logging
from db.database import get_service_counts, add_vacation_date
from services.services import services
from keyboards.admin_menu import admin_menu
from states.admin import AdminStates

router = Router()

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("Админ‑панель:", reply_markup=admin_menu())

@router.message(Command("stats"))
async def stats(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    parts = message.text.split()
    start_date = end_date = None
    if len(parts) == 3:
        start_date, end_date = parts[1], parts[2]

    counts = await get_service_counts(start_date, end_date)
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


@router.message(F.text == "🏖 Отпуск")
async def vacation_start(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("Введите дату начала отпуска (YYYY-MM-DD):")
    await state.set_state(AdminStates.vacation_start)


@router.message(AdminStates.vacation_start)
async def vacation_end(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        start = datetime.strptime(message.text, "%Y-%m-%d").date()
    except ValueError:
        await message.answer("Неверный формат даты. Используйте YYYY-MM-DD")
        return
    await state.update_data(vacation_start=start)
    await message.answer("Введите дату окончания отпуска (YYYY-MM-DD):")
    await state.set_state(AdminStates.vacation_end)


@router.message(AdminStates.vacation_end)
async def save_vacation(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    data = await state.get_data()
    try:
        end = datetime.strptime(message.text, "%Y-%m-%d").date()
    except ValueError:
        await message.answer("Неверный формат даты. Используйте YYYY-MM-DD")
        return
    start = data.get("vacation_start")
    if end < start:
        await message.answer("Дата окончания не может быть раньше начала. Попробуйте снова.")
        return
    current = start
    while current <= end:
        await add_vacation_date(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    await message.answer(f"Отпуск добавлен с {start} по {end}.")
    await state.clear()
