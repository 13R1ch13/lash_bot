from aiogram.fsm.state import StatesGroup, State

class AdminStates(StatesGroup):
    choosing_record = State()
    edit_record = State()
    waiting_new_datetime = State()
    confirm_update = State()
