from aiogram.fsm.state import StatesGroup, State


class AdminStates(StatesGroup):
    broadcast_message = State()
    view_records = State()
    vacation_start = State()
    vacation_end = State()
    stats_start = State()
    stats_end = State()
