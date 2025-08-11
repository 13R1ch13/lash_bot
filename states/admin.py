from aiogram.fsm.state import StatesGroup, State


class AdminStates(StatesGroup):
    broadcast_message = State()
