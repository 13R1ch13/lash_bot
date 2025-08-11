from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def appointments_keyboard(appointments):
    keyboard = [
        [KeyboardButton(text=f"{record[0]}. {record[4]} {record[5]} — {record[3]} ({record[2]})")]  # id, date, time, service, username
        for record in appointments
    ]
    keyboard.append([KeyboardButton(text="⬅️ Назад")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def edit_options_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✏️ Изменить"), KeyboardButton(text="🗑️ Удалить")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True,
    )


def confirm_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Подтвердить"), KeyboardButton(text="⬅️ Отмена")],
        ],
        resize_keyboard=True,
    )
