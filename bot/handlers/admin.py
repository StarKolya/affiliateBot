from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.filters import IsAdmin
from bot.handlers.states import CreateJobStates
from bot.keyboards.admin_kb import (
    admin_menu_kb,
    admin_niche_select_kb,
    application_status_kb,
    job_type_kb,
    jobs_menu_kb,
    skip_kb,
)
from bot.services import application_service, job_service
from bot.utils.logger import get_logger

logger = get_logger(__name__)

router = Router(name="admin")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    await message.answer("Welcome to the admin panel.", reply_markup=admin_menu_kb())


# --- Job management ---

@router.message(F.text == "💼 Jobs")
async def cmd_jobs_menu(message: Message) -> None:
    await message.answer("Job management:", reply_markup=jobs_menu_kb())


@router.callback_query(F.data == "admin_create_job")
async def callback_create_job(callback: CallbackQuery, state: FSMContext) -> None:
    niches = await job_service.list_all_niches()
    if not niches:
        await callback.answer("No niches exist yet. Add niches to the database first.", show_alert=True)
        return
    await state.set_state(CreateJobStates.select_niche)
    await callback.message.edit_text("Select a niche:", reply_markup=admin_niche_select_kb(niches))
    await callback.answer()


@router.callback_query(CreateJobStates.select_niche, F.data.startswith("admin_niche:"))
async def fsm_select_niche(callback: CallbackQuery, state: FSMContext) -> None:
    niche_id = int(callback.data.split(":")[1])
    await state.update_data(niche_id=niche_id)
    await state.set_state(CreateJobStates.enter_title)
    await callback.message.edit_text("Enter the job title:")
    await callback.answer()


@router.message(CreateJobStates.enter_title)
async def fsm_enter_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text)
    await state.set_state(CreateJobStates.select_type)
    await message.answer("Select job type:", reply_markup=job_type_kb())


@router.callback_query(CreateJobStates.select_type, F.data.startswith("admin_job_type:"))
async def fsm_select_type(callback: CallbackQuery, state: FSMContext) -> None:
    job_type = callback.data.split(":")[1]
    await state.update_data(job_type=job_type)
    await state.set_state(CreateJobStates.enter_description)
    await callback.message.edit_text(
        "Enter a description (or skip):", reply_markup=skip_kb()
    )
    await callback.answer()


@router.message(CreateJobStates.enter_description)
async def fsm_enter_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=message.text)
    await state.set_state(CreateJobStates.enter_commission)
    await message.answer("Enter the commission amount (numbers only):")


@router.callback_query(CreateJobStates.enter_description, F.data == "admin_skip")
async def fsm_skip_description(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(description=None)
    await state.set_state(CreateJobStates.enter_commission)
    await callback.message.edit_text("Enter the commission amount (numbers only):")
    await callback.answer()


@router.message(CreateJobStates.enter_commission)
async def fsm_enter_commission(message: Message, state: FSMContext) -> None:
    try:
        commission = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Please enter a valid number (e.g. 500 or 250.50):")
        return

    data = await state.get_data()
    await state.clear()

    job = await job_service.create_job_posting(
        niche_id=data["niche_id"],
        title=data["title"],
        job_type=data["job_type"],
        commission=commission,
        description=data.get("description"),
    )
    logger.info("Job created | id=%s title=%s", job.id, job.title)
    await message.answer(
        f"✅ Job <b>{job.title}</b> created successfully.",
        reply_markup=admin_menu_kb(),
    )


@router.callback_query(F.data == "admin_cancel")
async def callback_admin_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Cancelled.")
    await callback.answer()


# --- Application management ---

@router.message(F.text == "📋 Applications")
async def cmd_list_applications(message: Message) -> None:
    await _show_applications(message)


@router.callback_query(F.data == "admin_list_applications")
async def callback_list_applications(callback: CallbackQuery) -> None:
    await _show_applications(callback.message)
    await callback.answer()


async def _show_applications(target: Message) -> None:
    applications = await application_service.list_all_applications()
    if not applications:
        await target.answer("No applications yet.")
        return

    builder = InlineKeyboardBuilder()
    for app in applications:
        label = f"{app.account.name} — {app.job_posting.title} ({app.status.name})"
        builder.button(text=label, callback_data=f"admin_app:{app.id}")
    builder.adjust(1)
    await target.answer("Select an application:", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("admin_app:"))
async def callback_view_application(callback: CallbackQuery) -> None:
    application_id = int(callback.data.split(":")[1])
    app = await application_service.get_application(application_id)
    if app is None:
        await callback.answer("Application not found.", show_alert=True)
        return

    lines = [
        f"👤 {app.account.name}",
        f"💼 {app.job_posting.title}",
        f"📊 Status: {app.status.name}",
    ]

    answers = sorted(app.answers, key=lambda a: a.job_question_id)
    if answers:
        lines.append("")
        for answer in answers:
            lines.append(f"Q: {answer.job_question.question.description}")
            lines.append(f"A: {answer.answer}")

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=application_status_kb(app.id, app.status.name),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("app_status:"))
async def callback_update_status(callback: CallbackQuery) -> None:
    _, app_id, *status_parts = callback.data.split(":")
    new_status = ":".join(status_parts)
    try:
        app = await application_service.update_application_status(int(app_id), new_status)
    except ValueError as e:
        await callback.answer(str(e), show_alert=True)
        return

    await callback.message.edit_reply_markup(
        reply_markup=application_status_kb(app.id, app.status.name)
    )
    await callback.answer(f"Status updated to: {new_status}")


@router.callback_query(F.data == "app_status_noop")
async def callback_status_noop(callback: CallbackQuery) -> None:
    await callback.answer("Already set to this status.")


# --- Payout management ---

async def handle_list_payouts(message: Message) -> None:
    ...


async def handle_approve_payout(message: Message) -> None:
    ...


async def handle_reject_payout(message: Message) -> None:
    ...
