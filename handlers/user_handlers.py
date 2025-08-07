from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from keyboards.menu import main_menu
from states.booking import BookingStates
from services.services import services
from db.database import save_appointment, get_user_appointments
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import datetime

router = Router()

def service_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=s)] for s in services.keys()],
        resize_keyboard=True
    )

def date_keyboard():
    today = datetime.date.today()
    dates = []
    for i in range(14):
        day = today + datetime.timedelta(days=i)
        if day.weekday() in [0, 1, 3, 4, 5]:  # Пн, Вт, Чт, Пт, Сб
            dates.append([KeyboardButton(text=day.strftime("%Y-%m-%d"))])
    return ReplyKeyboardMarkup(keyboard=dates, resize_keyboard=True)

def time_keyboard(service_minutes):
    times = []
    for h in range(9, 19):
        for m in (0, 30):
            start = datetime.time(hour=h, minute=m)
            end_minutes = h * 60 + m + service_minutes
            if end_minutes <= 19 * 60:
                times.append([KeyboardButton(text=start.strftime("%H:%M"))])
    return ReplyKeyboardMarkup(keyboard=times, resize_keyboard=True)

@router.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Привет! Я бот для записи к мастеру. Выберите действие:", reply_markup=main_menu())

@router.message(F.text == "📝 Записаться")
async def book(message: Message, state: FSMContext):
    await message.answer("Выберите услугу:", reply_markup=service_keyboard())
    await state.set_state(BookingStates.choosing_service)

@router.message(BookingStates.choosing_service)
async def choose_service(message: Message, state: FSMContext):
    if message.text not in services:
        await message.answer("Пожалуйста, выбери услугу из списка.")
        return
    await state.update_data(service=message.text)
    await message.answer("Выберите дату:", reply_markup=date_keyboard())
    await state.set_state(BookingStates.choosing_date)

@router.message(BookingStates.choosing_date)
async def choose_date(message: Message, state: FSMContext):
    try:
        datetime.datetime.strptime(message.text, "%Y-%m-%d").date()
    except:
        await message.answer("Пожалуйста, выбери дату из списка.")
        return
    await state.update_data(date=message.text)
    data = await state.get_data()
    duration = services[data['service']]
    await message.answer("Выберите время:", reply_markup=time_keyboard(duration))
    await state.set_state(BookingStates.choosing_time)

@router.message(BookingStates.choosing_time)
async def choose_time(message: Message, state: FSMContext):
    try:
        datetime.datetime.strptime(message.text, "%H:%M")
    except:
        await message.answer("Пожалуйста, выбери время из списка.")
        return
    await state.update_data(time=message.text)
    data = await state.get_data()

    # Сохраняем в БД
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
