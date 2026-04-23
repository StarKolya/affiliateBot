from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.filters import IsAdmin
from bot.handlers.states import CreateJobStates, FilterApplicationsStates
from bot.keyboards.admin_kb import (
    APPS_PAGE_SIZE,
    QUESTIONS_PAGE_SIZE,
    admin_menu_kb,
    admin_niche_select_kb,
    application_filter_kb,
    application_status_kb,
    applications_page_kb,
    job_type_kb,
    jobs_menu_kb,
    question_select_kb,
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

    await state.update_data(commission=commission)
    data = await state.get_data()

    if data["job_type"] == "offer":
        await state.set_state(CreateJobStates.enter_commission_secondary)
        await message.answer(
            "Enter the commission for <b>Bought Course</b> status (or tap Skip):",
            reply_markup=skip_kb(),
        )
    else:
        await _show_question_select(message, state)


@router.callback_query(CreateJobStates.enter_commission_secondary, F.data == "admin_skip")
async def fsm_skip_commission_secondary(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(commission_secondary=None)
    await _show_question_select(callback.message, state)
    await callback.answer()


@router.message(CreateJobStates.enter_commission_secondary)
async def fsm_enter_commission_secondary(message: Message, state: FSMContext) -> None:
    try:
        commission_secondary = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Please enter a valid number or tap Skip:")
        return
    await state.update_data(commission_secondary=commission_secondary)
    await _show_question_select(message, state)


async def _show_question_select(target: Message, state: FSMContext) -> None:
    questions = await job_service.list_all_questions()
    if not questions:
        await _finish_create_job(target, state, selected_ids=[])
        return
    await state.update_data(selected_question_ids=[], question_page=0)
    await state.set_state(CreateJobStates.select_questions)
    total_pages = (len(questions) + QUESTIONS_PAGE_SIZE - 1) // QUESTIONS_PAGE_SIZE
    page_questions = questions[:QUESTIONS_PAGE_SIZE]
    await target.answer(
        "Choose questions to attach to this job:",
        reply_markup=question_select_kb(page_questions, set(), 0, total_pages),
    )


async def _finish_create_job(target: Message, state: FSMContext, selected_ids: list) -> None:
    data = await state.get_data()
    await state.clear()
    job = await job_service.create_job_posting(
        niche_id=data["niche_id"],
        title=data["title"],
        job_type=data["job_type"],
        commission=data["commission"],
        commission_secondary=data.get("commission_secondary"),
        description=data.get("description"),
    )
    questions = await job_service.list_all_questions()
    selected_set = set(selected_ids)
    for order, q in enumerate(q for q in questions if q.id in selected_set):
        await job_service.assign_question_to_job(job.id, q.id, order=order)
    logger.info("Job created | id=%s title=%s questions=%s", job.id, job.title, selected_ids)
    await target.answer(
        f"✅ Job <b>{job.title}</b> created successfully.",
        reply_markup=admin_menu_kb(),
    )


@router.callback_query(CreateJobStates.select_questions, F.data.startswith("admin_q_toggle:"))
async def fsm_toggle_question(callback: CallbackQuery, state: FSMContext) -> None:
    question_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    selected = set(data.get("selected_question_ids", []))
    if question_id in selected:
        selected.discard(question_id)
    else:
        selected.add(question_id)
    await state.update_data(selected_question_ids=list(selected))

    questions = await job_service.list_all_questions()
    page = data.get("question_page", 0)
    total_pages = (len(questions) + QUESTIONS_PAGE_SIZE - 1) // QUESTIONS_PAGE_SIZE
    page_questions = questions[page * QUESTIONS_PAGE_SIZE : (page + 1) * QUESTIONS_PAGE_SIZE]
    await callback.message.edit_reply_markup(
        reply_markup=question_select_kb(page_questions, selected, page, total_pages)
    )
    await callback.answer()


@router.callback_query(CreateJobStates.select_questions, F.data.startswith("admin_q_page:"))
async def fsm_question_page(callback: CallbackQuery, state: FSMContext) -> None:
    page = int(callback.data.split(":")[1])
    await state.update_data(question_page=page)
    data = await state.get_data()
    selected = set(data.get("selected_question_ids", []))

    questions = await job_service.list_all_questions()
    total_pages = (len(questions) + QUESTIONS_PAGE_SIZE - 1) // QUESTIONS_PAGE_SIZE
    page_questions = questions[page * QUESTIONS_PAGE_SIZE : (page + 1) * QUESTIONS_PAGE_SIZE]
    await callback.message.edit_reply_markup(
        reply_markup=question_select_kb(page_questions, selected, page, total_pages)
    )
    await callback.answer()


@router.callback_query(CreateJobStates.select_questions, F.data == "admin_q_confirm")
async def fsm_confirm_questions(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    selected_ids = data.get("selected_question_ids", [])
    await _finish_create_job(callback.message, state, selected_ids=selected_ids)
    await callback.answer()


@router.callback_query(F.data == "admin_cancel")
async def callback_admin_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Cancelled.")
    await callback.answer()


# --- Application management ---

@router.message(F.text == "📋 Applications")
async def cmd_list_applications(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _show_niche_picker(message)


@router.callback_query(F.data == "admin_list_applications")
async def callback_list_applications(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    niches = await job_service.list_all_niches()
    if not niches:
        await callback.message.edit_text("No niches found.")
        await callback.answer()
        return
    builder = InlineKeyboardBuilder()
    for niche in niches:
        builder.button(text=niche.name, callback_data=f"admin_apps_niche:{niche.id}")
    builder.adjust(1)
    await callback.message.edit_text("Select a niche:", reply_markup=builder.as_markup())
    await callback.answer()


async def _show_niche_picker(target: Message) -> None:
    niches = await job_service.list_all_niches()
    if not niches:
        await target.answer("No niches found.")
        return
    builder = InlineKeyboardBuilder()
    for niche in niches:
        builder.button(text=niche.name, callback_data=f"admin_apps_niche:{niche.id}")
    builder.adjust(1)
    await target.answer("Select a niche:", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("admin_apps_niche:"))
async def callback_apps_by_niche(callback: CallbackQuery, state: FSMContext) -> None:
    niche_id = int(callback.data.split(":")[1])
    jobs = await job_service.list_jobs_by_niche(niche_id)

    if len(jobs) > 1:
        builder = InlineKeyboardBuilder()
        builder.button(text="All jobs", callback_data=f"admin_apps_job:all:{niche_id}")
        for job in jobs:
            builder.button(text=job.title, callback_data=f"admin_apps_job:{job.id}:{niche_id}")
        builder.button(text="⬅️ Back", callback_data="admin_list_applications")
        builder.adjust(1)
        await callback.message.edit_text("Select a job:", reply_markup=builder.as_markup())
    else:
        job_id = jobs[0].id if jobs else None
        await _init_browse(callback, state, niche_id, job_id)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_apps_job:"))
async def callback_apps_by_job(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split(":")
    job_id_raw, niche_id = parts[1], int(parts[2])
    job_id = None if job_id_raw == "all" else int(job_id_raw)
    await _init_browse(callback, state, niche_id, job_id)
    await callback.answer()


async def _init_browse(
    callback: CallbackQuery, state: FSMContext, niche_id: int, job_id: int | None
) -> None:
    numeric_questions = []
    if job_id is not None:
        job = await job_service.get_job_with_questions(job_id)
        if job:
            numeric_questions = [
                {"jq_id": jq.id, "text": jq.question.description}
                for jq in sorted(job.job_questions, key=lambda jq: jq.order)
                if jq.question.expected_answer_type == "number"
            ]
    await state.update_data(
        niche_id=niche_id,
        job_id=job_id,
        numeric_questions=numeric_questions,
        page=0,
        filters={},
    )
    await _render_applications_page(callback.message, await state.get_data())


# --- Page navigation ---

@router.callback_query(F.data == "admin_apps_next")
async def callback_apps_next(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.update_data(page=data["page"] + 1)
    await _render_applications_page(callback.message, await state.get_data())
    await callback.answer()


@router.callback_query(F.data == "admin_apps_prev")
async def callback_apps_prev(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.update_data(page=max(0, data["page"] - 1))
    await _render_applications_page(callback.message, await state.get_data())
    await callback.answer()


@router.callback_query(F.data == "admin_apps_back")
async def callback_apps_back(callback: CallbackQuery, state: FSMContext) -> None:
    await _render_applications_page(callback.message, await state.get_data())
    await callback.answer()


# --- Filters ---

@router.callback_query(F.data == "admin_apps_filters")
async def callback_show_filters(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    numeric_questions = data.get("numeric_questions", [])
    if not numeric_questions:
        await callback.answer("No numeric filters available for this job.", show_alert=True)
        return
    await callback.message.edit_text(
        "Active filters:",
        reply_markup=application_filter_kb(numeric_questions, data.get("filters", {})),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_filter_set:"))
async def callback_filter_set(callback: CallbackQuery, state: FSMContext) -> None:
    jq_id = int(callback.data.split(":")[1])
    await state.set_state(FilterApplicationsStates.entering_filter)
    await state.update_data(pending_filter_jq_id=jq_id)
    data = await state.get_data()
    question = next(q for q in data["numeric_questions"] if q["jq_id"] == jq_id)
    await callback.message.edit_text(
        f"Enter minimum value for <b>{question['text']}</b>:"
    )
    await callback.answer()


@router.message(FilterApplicationsStates.entering_filter)
async def fsm_enter_filter_value(message: Message, state: FSMContext) -> None:
    try:
        min_val = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Please enter a valid number:")
        return

    data = await state.get_data()
    filters = data.get("filters", {})
    filters[str(data["pending_filter_jq_id"])] = min_val
    await state.update_data(filters=filters, page=0)
    await state.set_state(None)

    updated = await state.get_data()
    await message.answer(
        "Filter applied. Active filters:",
        reply_markup=application_filter_kb(updated["numeric_questions"], updated["filters"]),
    )


@router.callback_query(F.data == "admin_filter_clear")
async def callback_filter_clear(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(filters={}, page=0)
    data = await state.get_data()
    await callback.message.edit_text(
        "Filters cleared:",
        reply_markup=application_filter_kb(data["numeric_questions"], {}),
    )
    await callback.answer()


# --- Shared render ---

async def _render_applications_page(target: Message, data: dict) -> None:
    niche_id = data["niche_id"]
    job_id = data.get("job_id")
    page = data.get("page", 0)
    filters = {int(k): v for k, v in data.get("filters", {}).items()}

    if job_id is not None:
        applications = await application_service.list_applications_by_job(job_id)
        applications = application_service.apply_numeric_filters(applications, filters)
    else:
        applications = await application_service.list_applications_by_niche(niche_id)

    if not applications:
        await target.edit_text("No applications match the selected filters.")
        return

    total_pages = max(1, -(-len(applications) // APPS_PAGE_SIZE))
    page = min(page, total_pages - 1)
    page_apps = applications[page * APPS_PAGE_SIZE:(page + 1) * APPS_PAGE_SIZE]

    await target.edit_text(
        f"Applications (page {page + 1}/{total_pages}):",
        reply_markup=applications_page_kb(
            page_apps, page, total_pages, has_filters=bool(filters)
        ),
    )


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
        reply_markup=application_status_kb(app.id, app.status.name, app.job_posting.type),
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
        reply_markup=application_status_kb(app.id, app.status.name, app.job_posting.type)
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
