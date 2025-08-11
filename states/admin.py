from aiogram.fsm.state import StatesGroup, State


class AdminStates(StatesGroup):
    stats_range = State()
