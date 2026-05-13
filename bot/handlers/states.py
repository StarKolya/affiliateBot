from aiogram.fsm.state import State, StatesGroup


class ApplyStates(StatesGroup):
    answering = State()


class CreateJobStates(StatesGroup):
    select_niche = State()
    enter_title = State()
    select_type = State()
    enter_description = State()
    enter_commission = State()
    enter_commission_secondary = State()
    select_questions = State()


class FilterApplicationsStates(StatesGroup):
    entering_filter = State()


class CreateNicheStates(StatesGroup):
    enter_name = State()


class CreateReferralStates(StatesGroup):
    enter_name = State()
    select_type = State()
    select_job = State()


class RequestPayoutStates(StatesGroup):
    enter_amount = State()


class AdminPayStates(StatesGroup):
    enter_amount = State()


class CreateQuestionStates(StatesGroup):
    enter_title = State()
    enter_description = State()
    select_answer_type = State()
