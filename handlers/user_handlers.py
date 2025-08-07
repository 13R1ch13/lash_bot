from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from keyboards.menu import main_menu
from states.booking import BookingStates
from services.services import services
from db.database import (
    save_appointment,
    get_user_appointments,
    is_time_range_available,
    delete_user_appointment,
)
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import datetime

router = Router()

# ---------- Клавиатуры ----------
def service_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=s)] for s in services.keys()] + [[KeyboardButton(text="⬅️ Назад")]],
        resize_keyboard=True
    )

def date_keyboard():
    today = datetime.date.today()
    dates = []
    for i in range(14):
        day = today + datetime.timedelta(days=i)
        if day.weekday() in [0, 1, 3, 4, 5]:  # Пн, Вт, Чт, Пт, Сб
            dates.append([KeyboardButton(text=day.strftime("%Y-%m-%d"))])
    dates.append([KeyboardButton(text="⬅️ Назад")])
    return ReplyKeyboardMarkup(keyboard=dates, resize_keyboard=True)

def time_keyboard(date, service_minutes):
    times = []
    for h in range(9, 19):
        for m in (0, 30):
            start = datetime.time(hour=h, minute=m)
            start_minutes = h * 60 + m
            end_minutes = start_minutes + service_minutes

            if end_minutes > 19 * 60:  # мастер работает до 19:00
                continue

            start_str = start.strftime("%H:%M")
            if is_time_range_available(date, start_str, service_minutes):
                times.append([KeyboardButton(text=start_str)])

    if not times:
        times = [[KeyboardButton(text="Нет свободного времени")]]
    times.append([KeyboardButton(text="⬅️ Назад")])
    return ReplyKeyboardMarkup(keyboard=times, resize_keyboard=True)

# ---------- Старт ----------
@router.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Привет! Я бот для записи к мастеру. Выберите действие:", reply_markup=main_menu())

# ---------- Запись: старт ----------
@router.message(F.text == "📝 Записаться")
async def book(message: Message, state: FSMContext):
    await message.answer("Выберите услугу:", reply_markup=service_keyboard())
    await state.set_state(BookingStates.choosing_service)

# ---------- Выбор услуги ----------
@router.message(BookingStates.choosing_service)
async def choose_service(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await state.clear()
        await message.answer("Главное меню", reply_markup=main_menu())
        return

    if message.text not in services:
        await message.answer("Пожалуйста, выбери услугу из списка.")
        return

    await state.update_data(service=message.text)
    await message.answer(
        "📅 Выберите дату из списка или введите вручную в формате: 2025-09-01",
        reply_markup=date_keyboard()
    )
    await state.set_state(BookingStates.choosing_date)

# ---------- Выбор даты (в том числе ручной ввод) ----------
@router.message(BookingStates.choosing_date)
async def choose_date(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await message.answer("Выберите услугу:", reply_markup=service_keyboard())
        await state.set_state(BookingStates.choosing_service)
        return

    try:
        selected_date = datetime.datetime.strptime(message.text, "%Y-%m-%d").date()
    except ValueError:
        await message.answer("❌ Неверный формат даты. Введите в формате: 2025-09-01")
        return

    if selected_date < datetime.date.today():
        await message.answer("❌ Нельзя выбрать прошедшую дату.")
        return

    await state.update_data(date=message.text)
    data = await state.get_data()
    duration = services[data['service']]

    await message.answer(
        f"Вы выбрали: {message.text}\nТеперь выберите время:",
        reply_markup=time_keyboard(message.text, duration)
    )
    await state.set_state(BookingStates.choosing_time)

# ---------- Выбор времени ----------
@router.message(BookingStates.choosing_time)
async def choose_time(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        data = await state.get_data()
        await message.answer(
            "📅 Выберите дату из списка или введите вручную в формате: 2025-09-01",
            reply_markup=date_keyboard()
        )
        await state.set_state(BookingStates.choosing_date)
        return

    try:
        datetime.datetime.strptime(message.text, "%H:%M")
    except:
        await message.answer("Пожалуйста, выбери время из списка.")
        return

    await state.update_data(time=message.text)
    data = await state.get_data()

    duration = services[data['service']]
    if not is_time_range_available(data["date"], data["time"], duration):
        await message.answer("⛔ Это время уже занято. Пожалуйста, выбери другое.")
        return

    save_appointment(
        user_id=message.from_user.id,
        username=message.from_user.username or "unknown",
        service=data["service"],
        date=data["date"],
        time=data["time"]
    )

    record = f"✅ Запись подтверждена:\nУслуга: {data['service']}\nДата: {data['date']}\nВремя: {data['time']}"
    await message.answer(record, reply_markup=main_menu())
    await state.clear()

# ---------- Просмотр записей ----------
@router.message(F.text == "📅 Мои записи")
async def show_my_appointments(message: Message):
    records = get_user_appointments(message.from_user.id)
    if not records:
        await message.answer("У вас пока нет записей.")
        return

    text = "📋 Ваши записи:\n\n"
    for service, date, time in records:
        text += f"• {service} — {date} в {time}\n"
    await message.answer(text)

# ---------- Отмена записи ----------
@router.message(F.text == "❌ Отменить запись")
async def cancel_booking(message: Message, state: FSMContext):
    records = get_user_appointments(message.from_user.id)
    if not records:
        await message.answer("У вас нет активных записей.")
        return

    keyboard = [[KeyboardButton(text=f"{service} — {date} в {time}")]
                for service, date, time in records]
    keyboard.append([KeyboardButton(text="⬅️ Назад")])

    await message.answer("Выберите запись, которую хотите отменить:", reply_markup=ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    ))
    await state.set_state(BookingStates.confirming)

# ---------- Подтверждение отмены ----------
@router.message(BookingStates.confirming)
async def confirm_cancel(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await message.answer("Главное меню", reply_markup=main_menu())
        await state.clear()
        return

    try:
        parts = message.text.split(" — ")
        service = parts[0]
        date, time = parts[1].split(" в ")
    except:
        await message.answer("Формат записи неверный. Пожалуйста, выберите из списка.")
        return

    delete_user_appointment(message.from_user.id, service, date, time)
    await message.answer("❌ Запись отменена.", reply_markup=main_menu())
    await state.clear()
