from aiogram.fsm.state import State, StatesGroup


class ApplyStates(StatesGroup):
    answering = State()


class CreateJobStates(StatesGroup):
    select_niche = State()
    enter_title = State()
    select_type = State()
    enter_description = State()
    enter_commission = State()
