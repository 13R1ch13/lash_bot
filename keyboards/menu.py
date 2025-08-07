from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Записаться")],
            [KeyboardButton(text="📅 Мои записи")],
            [KeyboardButton(text="❌ Отменить запись")]
        ],
        resize_keyboard=True
    )
