from aiogram.fsm.state import State, StatesGroup


class ApplyStates(StatesGroup):
    answering = State()
