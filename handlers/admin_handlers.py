from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from config import ADMIN_IDS
from bot import bot
from db.user_storage import get_all_users
import logging
from db.database import (
    get_service_counts,
    get_all_appointments,
    update_appointment,
    delete_user_appointment,
)
from services.services import services
from keyboards.admin import (
    appointments_keyboard,
    edit_options_keyboard,
    confirm_keyboard,
)
from states.admin import AdminStates
from datetime import datetime

router = Router()

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


@router.message(F.text == "✍️ Записи")
async def show_appointments(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    appointments = await get_all_appointments()
    if not appointments:
        await message.answer("Записей нет.")
        return
    await state.update_data(appointments=appointments)
    await message.answer(
        "Выберите запись:", reply_markup=appointments_keyboard(appointments)
    )
    await state.set_state(AdminStates.choosing_record)


@router.message(AdminStates.choosing_record)
async def choose_record(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await state.clear()
        return
    data = await state.get_data()
    appointments = {rec[0]: rec for rec in data.get("appointments", [])}
    try:
        rec_id = int(message.text.split(".")[0])
    except ValueError:
        await message.answer("Пожалуйста, выберите запись из списка.")
        return
    if rec_id not in appointments:
        await message.answer("Пожалуйста, выберите запись из списка.")
        return
    record = appointments[rec_id]
    await state.update_data(selected_record=record)
    text = f"{record[4]} {record[5]} — {record[3]} ({record[2]})"
    await message.answer(text, reply_markup=edit_options_keyboard())
    await state.set_state(AdminStates.edit_record)


@router.message(AdminStates.edit_record)
async def edit_record(message: Message, state: FSMContext):
    data = await state.get_data()
    if message.text == "⬅️ Назад":
        appointments = data.get("appointments", [])
        await message.answer(
            "Выберите запись:", reply_markup=appointments_keyboard(appointments)
        )
        await state.set_state(AdminStates.choosing_record)
        return
    record = data.get("selected_record")
    if message.text == "🗑️ Удалить":
        await delete_user_appointment(record[1], record[3], record[4], record[5])
        appointments = await get_all_appointments()
        if appointments:
            await state.update_data(appointments=appointments)
            await message.answer(
                "Запись удалена. Выберите запись:",
                reply_markup=appointments_keyboard(appointments),
            )
            await state.set_state(AdminStates.choosing_record)
        else:
            await state.clear()
            await message.answer("Записей больше нет.")
        return
    if message.text == "✏️ Изменить":
        await message.answer("Введите новую дату и время (YYYY-MM-DD HH:MM):")
        await state.set_state(AdminStates.waiting_new_datetime)
        return
    await message.answer("Пожалуйста, выберите действие из меню.")


@router.message(AdminStates.waiting_new_datetime)
async def wait_new_datetime(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await message.answer("Что сделать?", reply_markup=edit_options_keyboard())
        await state.set_state(AdminStates.edit_record)
        return
    try:
        new_date, new_time = message.text.split()
        datetime.strptime(new_date, "%Y-%m-%d")
        datetime.strptime(new_time, "%H:%M")
    except Exception:
        await message.answer(
            "Неверный формат. Введите в формате YYYY-MM-DD HH:MM"
        )
        return
    await state.update_data(new_date=new_date, new_time=new_time)
    await message.answer(
        f"Изменить на {new_date} {new_time}?", reply_markup=confirm_keyboard()
    )
    await state.set_state(AdminStates.confirm_update)


@router.message(AdminStates.confirm_update)
async def confirm_update_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    if message.text == "✅ Подтвердить":
        record = data.get("selected_record")
        await update_appointment(
            record[0], date=data["new_date"], time=data["new_time"]
        )
        appointments = await get_all_appointments()
        if appointments:
            await state.update_data(appointments=appointments)
            await message.answer(
                "Запись обновлена. Выберите запись:",
                reply_markup=appointments_keyboard(appointments),
            )
            await state.set_state(AdminStates.choosing_record)
        else:
            await state.clear()
            await message.answer("Записей нет.")
        return
    if message.text == "⬅️ Отмена":
        await message.answer("Изменение отменено.", reply_markup=edit_options_keyboard())
        await state.set_state(AdminStates.edit_record)
        return
    await message.answer("Пожалуйста, выберите действие из меню.")
