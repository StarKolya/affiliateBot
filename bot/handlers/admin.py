from decimal import Decimal

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.filters import IsAdmin
from bot.handlers.states import AdminPayStates, CreateJobStates, CreateNicheStates, CreateQuestionStates, FilterApplicationsStates
from bot.keyboards.admin_kb import (
    APPS_PAGE_SIZE,
    FINANCE_PAGE_SIZE,
    QUESTIONS_PAGE_SIZE,
    REFERRERS_PAGE_SIZE,
    _STATUS_DISPLAY_RU,
    _JOB_TYPE_RU,
    admin_menu_kb,
    admin_niche_select_kb,
    application_filter_kb,
    application_sort_kb,
    application_status_kb,
    applications_page_kb,
    finance_list_kb,
    job_manage_detail_kb,
    job_type_kb,
    jobs_manage_list_kb,
    jobs_manage_niche_kb,
    jobs_menu_kb,
    niche_delete_confirm_kb,
    niche_detail_kb,
    niches_manage_kb,
    payout_action_kb,
    question_answer_type_kb,
    question_delete_confirm_kb,
    question_detail_kb,
    question_select_kb,
    questions_list_kb,
    referrals_menu_kb,
    referrer_detail_kb,
    referrers_list_kb,
    skip_kb,
)
from bot.services import application_service, job_service, payout_service, referral_service
from bot.models.account import Account
from bot.models.referral import Referral
from bot.utils.logger import get_logger

logger = get_logger(__name__)

router = Router(name="admin")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

_STATUS_LABEL = {"active": "🟢 Активна", "paused": "🟡 Приостановлена", "closed": "🔴 Закрыта"}


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    await message.answer("Добро пожаловать в панель администратора.", reply_markup=admin_menu_kb())


# --- Job management ---

@router.message(F.text == "💼 Вакансии")
async def cmd_jobs_menu(message: Message) -> None:
    await message.answer("Управление вакансиями:", reply_markup=jobs_menu_kb())


@router.callback_query(F.data == "admin_create_job")
async def callback_create_job(callback: CallbackQuery, state: FSMContext) -> None:
    niches = await job_service.list_all_niches()
    if not niches:
        await callback.answer("Ниши ещё не созданы. Сначала добавьте ниши.", show_alert=True)
        return
    await state.set_state(CreateJobStates.select_niche)
    await callback.message.edit_text("Выберите нишу:", reply_markup=admin_niche_select_kb(niches))
    await callback.answer()


@router.callback_query(CreateJobStates.select_niche, F.data.startswith("admin_niche:"))
async def fsm_select_niche(callback: CallbackQuery, state: FSMContext) -> None:
    niche_id = int(callback.data.split(":")[1])
    await state.update_data(niche_id=niche_id)
    await state.set_state(CreateJobStates.enter_title)
    await callback.message.edit_text("Введите название вакансии:")
    await callback.answer()


@router.message(CreateJobStates.enter_title)
async def fsm_enter_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text)
    await state.set_state(CreateJobStates.select_type)
    await message.answer("Выберите тип вакансии:", reply_markup=job_type_kb())


@router.callback_query(CreateJobStates.select_type, F.data.startswith("admin_job_type:"))
async def fsm_select_type(callback: CallbackQuery, state: FSMContext) -> None:
    job_type = callback.data.split(":")[1]
    await state.update_data(job_type=job_type)
    await state.set_state(CreateJobStates.enter_description)
    await callback.message.edit_text(
        "Введите описание (или пропустите):", reply_markup=skip_kb()
    )
    await callback.answer()


@router.message(CreateJobStates.enter_description)
async def fsm_enter_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=message.text)
    await state.set_state(CreateJobStates.enter_commission)
    await message.answer("Введите размер комиссии (только цифры):")


@router.callback_query(CreateJobStates.enter_description, F.data == "admin_skip")
async def fsm_skip_description(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(description=None)
    await state.set_state(CreateJobStates.enter_commission)
    await callback.message.edit_text("Введите размер комиссии (только цифры):")
    await callback.answer()


@router.message(CreateJobStates.enter_commission)
async def fsm_enter_commission(message: Message, state: FSMContext) -> None:
    try:
        commission = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Введите корректное число (например, 500 или 250.50):")
        return

    await state.update_data(commission=commission)
    data = await state.get_data()

    if data["job_type"] == "offer":
        await state.set_state(CreateJobStates.enter_commission_secondary)
        await message.answer(
            "Введите комиссию для статуса <b>Купил курс</b> (или пропустите):",
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
        await message.answer("Введите корректное число или нажмите «Пропустить»:")
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
        "Выберите вопросы для этой вакансии:",
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
        f"✅ Вакансия <b>{job.title}</b> успешно создана.",
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
    await callback.message.edit_text("Отменено.")
    await callback.answer()


# --- Application management ---

@router.message(F.text == "📋 Отклики")
async def cmd_list_applications(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _show_niche_picker(message)


@router.callback_query(F.data == "admin_list_applications")
async def callback_list_applications(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    niches = await job_service.list_all_niches()
    if not niches:
        await callback.message.edit_text("Ниши не найдены.")
        await callback.answer()
        return
    builder = InlineKeyboardBuilder()
    for niche in niches:
        builder.button(text=niche.name, callback_data=f"admin_apps_niche:{niche.id}")
    builder.adjust(1)
    await callback.message.edit_text("Выберите нишу:", reply_markup=builder.as_markup())
    await callback.answer()


async def _show_niche_picker(target: Message) -> None:
    niches = await job_service.list_all_niches()
    if not niches:
        await target.answer("Ниши не найдены.")
        return
    builder = InlineKeyboardBuilder()
    for niche in niches:
        builder.button(text=niche.name, callback_data=f"admin_apps_niche:{niche.id}")
    builder.adjust(1)
    await target.answer("Выберите нишу:", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("admin_apps_niche:"))
async def callback_apps_by_niche(callback: CallbackQuery, state: FSMContext) -> None:
    niche_id = int(callback.data.split(":")[1])
    jobs = await job_service.list_jobs_by_niche(niche_id)

    if len(jobs) > 1:
        builder = InlineKeyboardBuilder()
        builder.button(text="Все вакансии", callback_data=f"admin_apps_job:all:{niche_id}")
        for job in jobs:
            builder.button(text=job.title, callback_data=f"admin_apps_job:{job.id}:{niche_id}")
        builder.button(text="⬅️ Назад", callback_data="admin_list_applications")
        builder.adjust(1)
        await callback.message.edit_text("Выберите вакансию:", reply_markup=builder.as_markup())
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
        await callback.answer("Нет числовых фильтров для этой вакансии.", show_alert=True)
        return
    await callback.message.edit_text(
        "Активные фильтры:",
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
        f"Введите минимальное значение для <b>{question['text']}</b>:"
    )
    await callback.answer()


@router.message(FilterApplicationsStates.entering_filter)
async def fsm_enter_filter_value(message: Message, state: FSMContext) -> None:
    try:
        min_val = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Введите корректное число:")
        return

    data = await state.get_data()
    filters = data.get("filters", {})
    filters[str(data["pending_filter_jq_id"])] = min_val
    await state.update_data(filters=filters, page=0)
    await state.set_state(None)

    updated = await state.get_data()
    await message.answer(
        "Фильтр применён. Активные фильтры:",
        reply_markup=application_filter_kb(updated["numeric_questions"], updated["filters"]),
    )


@router.callback_query(F.data == "admin_filter_clear")
async def callback_filter_clear(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(filters={}, page=0)
    data = await state.get_data()
    await callback.message.edit_text(
        "Фильтры сброшены:",
        reply_markup=application_filter_kb(data["numeric_questions"], {}),
    )
    await callback.answer()


# --- Sorting ---

@router.callback_query(F.data == "admin_apps_sort")
async def callback_show_sort(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await callback.message.edit_text(
        "Сортировка:",
        reply_markup=application_sort_kb(
            data.get("numeric_questions", []),
            data.get("sort_by"),
            data.get("sort_ascending", True),
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_sort_set:"))
async def callback_sort_set(callback: CallbackQuery, state: FSMContext) -> None:
    key = callback.data.split(":")[1]
    await state.update_data(sort_by=key, sort_ascending=True, page=0)
    data = await state.get_data()
    await callback.message.edit_text(
        "Сортировка:",
        reply_markup=application_sort_kb(data.get("numeric_questions", []), key, True),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_sort_toggle:"))
async def callback_sort_toggle(callback: CallbackQuery, state: FSMContext) -> None:
    key = callback.data.split(":")[1]
    data = await state.get_data()
    ascending = not data.get("sort_ascending", True)
    await state.update_data(sort_ascending=ascending, page=0)
    await callback.message.edit_reply_markup(
        reply_markup=application_sort_kb(data.get("numeric_questions", []), key, ascending)
    )
    await callback.answer()


@router.callback_query(F.data == "admin_sort_clear")
async def callback_sort_clear(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(sort_by=None, sort_ascending=True, page=0)
    data = await state.get_data()
    await callback.message.edit_text(
        "Сортировка сброшена:",
        reply_markup=application_sort_kb(data.get("numeric_questions", []), None, True),
    )
    await callback.answer()


# --- Shared render ---

async def _render_applications_page(target: Message, data: dict) -> None:
    niche_id = data["niche_id"]
    job_id = data.get("job_id")
    page = data.get("page", 0)
    filters = {int(k): v for k, v in data.get("filters", {}).items()}
    sort_by = data.get("sort_by")
    ascending = data.get("sort_ascending", True)

    if job_id is not None:
        applications = await application_service.list_applications_by_job(job_id)
        applications = application_service.apply_numeric_filters(applications, filters)
    else:
        applications = await application_service.list_applications_by_niche(niche_id)

    if sort_by:
        applications = application_service.apply_sort(applications, sort_by, ascending)

    if not applications:
        await target.edit_text("Нет откликов по выбранным фильтрам.")
        return

    total_pages = max(1, -(-len(applications) // APPS_PAGE_SIZE))
    page = min(page, total_pages - 1)
    page_apps = applications[page * APPS_PAGE_SIZE:(page + 1) * APPS_PAGE_SIZE]

    await target.edit_text(
        f"Отклики (стр. {page + 1}/{total_pages}):",
        reply_markup=applications_page_kb(
            page_apps, page, total_pages, has_filters=bool(filters), has_sort=bool(sort_by)
        ),
    )


@router.callback_query(F.data.startswith("admin_app:"))
async def callback_view_application(callback: CallbackQuery) -> None:
    application_id = int(callback.data.split(":")[1])
    app = await application_service.get_application(application_id)
    if app is None:
        await callback.answer("Отклик не найден.", show_alert=True)
        return

    status_ru = _STATUS_DISPLAY_RU.get(app.status.name, app.status.name)
    job_type_ru = _JOB_TYPE_RU.get(app.job_posting.type, app.job_posting.type)
    name = app.account.name
    tg_id = app.account.telegram_id
    contact = f'<a href="tg://user?id={tg_id}">{name}</a>'
    if app.account.username:
        contact += f" (@{app.account.username})"

    lines = [
        f"👤 {contact}",
        f"💼 {app.job_posting.title}",
        f"🏷 Тип: {job_type_ru}",
        f"📊 Статус: {status_ru}",
    ]

    answers = sorted(app.answers, key=lambda a: a.job_question_id)
    if answers:
        lines.append("")
        for answer in answers:
            lines.append(f"В: {answer.job_question.question.description}")
            lines.append(f"О: {answer.answer}")

    await callback.message.edit_text(
        "\n".join(lines),
        parse_mode="HTML",
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
    status_ru = _STATUS_DISPLAY_RU.get(new_status, new_status)
    await callback.answer(f"Статус обновлён: {status_ru}")


@router.callback_query(F.data == "app_status_noop")
async def callback_status_noop(callback: CallbackQuery) -> None:
    await callback.answer("Статус уже установлен.")


# --- Jobs menu callback (for back buttons) ---

@router.callback_query(F.data == "admin_jobs_menu")
async def callback_jobs_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text("Управление вакансиями:", reply_markup=jobs_menu_kb())
    await callback.answer()


# --- Job enable / disable ---

@router.callback_query(F.data == "admin_manage_jobs")
async def callback_manage_jobs(callback: CallbackQuery) -> None:
    niches = await job_service.list_all_niches()
    if not niches:
        await callback.answer("Ниши ещё не созданы.", show_alert=True)
        return
    await callback.message.edit_text("Выберите нишу:", reply_markup=jobs_manage_niche_kb(niches))
    await callback.answer()


@router.callback_query(F.data.startswith("admin_manage_jobs_niche:"))
async def callback_manage_jobs_niche(callback: CallbackQuery) -> None:
    niche_id = int(callback.data.split(":")[1])
    jobs = await job_service.list_all_jobs_by_niche(niche_id)
    if not jobs:
        await callback.answer("В этой нише нет вакансий.", show_alert=True)
        return
    await callback.message.edit_text(
        "Выберите вакансию:",
        reply_markup=jobs_manage_list_kb(jobs, niche_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_manage_job:"))
async def callback_manage_job_detail(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    job_id, niche_id = int(parts[1]), int(parts[2])
    job = await job_service.get_job(job_id)
    status_label = _STATUS_LABEL.get(job.status, job.status)
    job_type_ru = _JOB_TYPE_RU.get(job.type, job.type)
    await callback.message.edit_text(
        f"💼 <b>{job.title}</b>\nТип: {job_type_ru}\nСтатус: {status_label}",
        reply_markup=job_manage_detail_kb(job_id, job.status, niche_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_job_toggle:"))
async def callback_job_toggle_status(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    job_id, niche_id = int(parts[1]), int(parts[2])
    job = await job_service.get_job(job_id)
    new_status = "paused" if job.status == "active" else "active"
    job = await job_service.set_job_status(job_id, new_status)
    status_label = _STATUS_LABEL.get(job.status, job.status)
    job_type_ru = _JOB_TYPE_RU.get(job.type, job.type)
    await callback.message.edit_text(
        f"💼 <b>{job.title}</b>\nТип: {job_type_ru}\nСтатус: {status_label}",
        reply_markup=job_manage_detail_kb(job_id, job.status, niche_id),
    )
    await callback.answer()


# --- Niche management ---

@router.message(F.text == "🏷 Ниши")
async def cmd_niches_menu(message: Message) -> None:
    niches = await job_service.list_all_niches()
    await message.answer("Управление нишами:", reply_markup=niches_manage_kb(niches))


@router.callback_query(F.data == "admin_niches_menu")
async def callback_niches_menu(callback: CallbackQuery) -> None:
    niches = await job_service.list_all_niches()
    await callback.message.edit_text("Управление нишами:", reply_markup=niches_manage_kb(niches))
    await callback.answer()


@router.callback_query(F.data == "admin_create_niche")
async def callback_create_niche(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CreateNicheStates.enter_name)
    await callback.message.edit_text("Введите название ниши:")
    await callback.answer()


@router.message(CreateNicheStates.enter_name)
async def fsm_enter_niche_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    await job_service.create_niche(name)
    await state.clear()
    niches = await job_service.list_all_niches()
    await message.answer(f"✅ Ниша <b>{name}</b> создана.", reply_markup=niches_manage_kb(niches))


@router.callback_query(F.data.startswith("admin_niche_detail:"))
async def callback_niche_detail(callback: CallbackQuery) -> None:
    niche_id = int(callback.data.split(":")[1])
    niche = await job_service.get_niche(niche_id)
    job_count = await job_service.count_jobs_by_niche(niche_id)
    await callback.message.edit_text(
        f"🏷 <b>{niche.name}</b>\nВакансий: {job_count}",
        reply_markup=niche_detail_kb(niche_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_niche_delete:"))
async def callback_niche_delete(callback: CallbackQuery) -> None:
    niche_id = int(callback.data.split(":")[1])
    job_count = await job_service.count_jobs_by_niche(niche_id)
    if job_count > 0:
        text = (
            f"⚠️ В этой нише <b>{job_count}</b> вак. Удаление отключит все связанные вакансии.\n\n"
            "Вы уверены?"
        )
    else:
        text = "Вы уверены, что хотите удалить эту нишу?"
    await callback.message.edit_text(text, reply_markup=niche_delete_confirm_kb(niche_id))
    await callback.answer()


@router.callback_query(F.data.startswith("admin_niche_delete_confirm:"))
async def callback_niche_delete_confirm(callback: CallbackQuery) -> None:
    niche_id = int(callback.data.split(":")[1])
    await job_service.delete_niche(niche_id)
    niches = await job_service.list_all_niches()
    await callback.message.edit_text("✅ Ниша удалена.", reply_markup=niches_manage_kb(niches))
    await callback.answer()


# --- Referrals ---

@router.message(F.text == "🔗 Рефералы")
async def cmd_referrals_menu(message: Message) -> None:
    overview = await referral_service.get_admin_overview()
    await message.answer(
        f"🔗 <b>Реферальная сводка</b>\n\n"
        f"👤 Рефереров: {overview['total_referrers']}\n"
        f"👥 Привлечено пользователей: {overview['total_referred']}\n"
        f"📝 Откликов по рефералам: {overview['total_applications']}\n"
        f"💰 Всего заработано: ${overview['total_earned']:.2f}\n"
        f"⏳ Ожидает выплаты: {overview['pending_payout_count']} (${overview['pending_payout_amount']:.2f})",
        reply_markup=referrals_menu_kb(),
    )


@router.callback_query(F.data == "admin_referrals_menu")
async def callback_referrals_menu(callback: CallbackQuery) -> None:
    overview = await referral_service.get_admin_overview()
    await callback.message.edit_text(
        f"🔗 <b>Реферальная сводка</b>\n\n"
        f"👤 Рефереров: {overview['total_referrers']}\n"
        f"👥 Привлечено пользователей: {overview['total_referred']}\n"
        f"📝 Откликов по рефералам: {overview['total_applications']}\n"
        f"💰 Всего заработано: ${overview['total_earned']:.2f}\n"
        f"⏳ Ожидает выплаты: {overview['pending_payout_count']} (${overview['pending_payout_amount']:.2f})",
        reply_markup=referrals_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_all_referrers")
async def callback_all_referrers(callback: CallbackQuery) -> None:
    await _show_referrers_page(callback.message, page=0)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_referrers_page:"))
async def callback_referrers_page(callback: CallbackQuery) -> None:
    page = int(callback.data.split(":")[1])
    await _show_referrers_page(callback.message, page=page)
    await callback.answer()


async def _show_referrers_page(target: Message, page: int) -> None:
    accounts = await Account.filter(referrals__isnull=False).distinct().order_by("name")
    total_pages = max(1, -(-len(accounts) // REFERRERS_PAGE_SIZE))
    page = min(page, total_pages - 1)
    page_accounts = accounts[page * REFERRERS_PAGE_SIZE:(page + 1) * REFERRERS_PAGE_SIZE]
    text = (
        f"👥 <b>Все рефереры</b>  (стр. {page + 1}/{total_pages})"
        if accounts else
        "👥 <b>Все рефереры</b>\n\nРефереров пока нет."
    )
    await target.edit_text(text, reply_markup=referrers_list_kb(page_accounts, page, total_pages))


@router.callback_query(F.data.startswith("admin_referrer:"))
async def callback_referrer_detail(callback: CallbackQuery) -> None:
    account_id = int(callback.data.split(":")[1])
    account = await Account.get_or_none(id=account_id)
    if account is None:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return
    stats = await referral_service.get_account_stats(account_id)
    links = await referral_service.list_user_referrals(account_id)
    tag = f"@{account.username}" if account.username else account.name
    await callback.message.edit_text(
        f"👤 <b>{account.name}</b>  {tag}\n\n"
        f"🔗 Ссылок: {len(links)}\n"
        f"👥 Активации: {stats.total_referred}\n"
        f"📝 Отклики: {stats.total_applications}\n"
        f"⌛️ В обработке: {stats.total_pending}\n"
        f"🪫 Отклонено: {stats.total_declined}\n"
        f"✅ Принято: {stats.total_joined_team}\n"
        f"📚 Обучение: {stats.total_bought_course}\n"
        f"💰 Доход: ${stats.total_earned:.2f}",
        reply_markup=referrer_detail_kb(account_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_pay_user:"))
async def callback_pay_user(callback: CallbackQuery, state: FSMContext) -> None:
    account_id = int(callback.data.split(":")[1])
    summary = await payout_service.get_user_summary(account_id)
    if summary.available_amount <= 0:
        await callback.answer("Нет доступных средств для выплаты.", show_alert=True)
        return
    await state.set_state(AdminPayStates.enter_amount)
    await state.update_data(pay_account_id=account_id)
    await callback.message.edit_text(
        f"💳 Введите сумму для выплаты\n"
        f"(доступно: ${summary.available_amount:.2f}):"
    )
    await callback.answer()


@router.message(AdminPayStates.enter_amount)
async def fsm_admin_pay_amount(message: Message, state: FSMContext) -> None:
    try:
        amount = Decimal(message.text.replace(",", "."))
    except Exception:
        await message.answer("Введите корректное число:")
        return

    data = await state.get_data()
    account_id = data["pay_account_id"]
    await state.clear()

    try:
        await payout_service.admin_pay_account(account_id, amount)
    except ValueError as e:
        await message.answer(str(e))
        return

    account = await Account.get_or_none(id=account_id)
    tag = f"@{account.username}" if account and account.username else (account.name if account else str(account_id))
    await message.answer(
        f"✅ Выплата ${amount:.2f} для {tag} зафиксирована.",
        reply_markup=admin_menu_kb(),
    )


@router.callback_query(F.data == "admin_finance")
async def callback_finance(callback: CallbackQuery) -> None:
    await _show_finance_page(callback.message, page=0)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_finance_page:"))
async def callback_finance_page(callback: CallbackQuery) -> None:
    page = int(callback.data.split(":")[1])
    await _show_finance_page(callback.message, page=page)
    await callback.answer()


async def _show_finance_page(target: Message, page: int) -> None:
    payouts = await payout_service.list_pending_payouts()
    total_pages = max(1, -(-len(payouts) // FINANCE_PAGE_SIZE))
    page = min(page, total_pages - 1)
    page_payouts = payouts[page * FINANCE_PAGE_SIZE:(page + 1) * FINANCE_PAGE_SIZE]
    text = (
        f"💰 <b>Запросы на выплату</b>  (стр. {page + 1}/{total_pages})"
        if payouts else
        "💰 <b>Запросы на выплату</b>\n\nНет ожидающих запросов."
    )
    await target.edit_text(text, reply_markup=finance_list_kb(page_payouts, page, total_pages))


@router.callback_query(F.data.startswith("admin_payout:"))
async def callback_payout_detail(callback: CallbackQuery) -> None:
    payout_id = int(callback.data.split(":")[1])
    payouts = await payout_service.list_pending_payouts()
    payout = next((p for p in payouts if p.id == payout_id), None)
    if payout is None:
        await callback.answer("Запрос не найден или уже обработан.", show_alert=True)
        return
    tag = f"@{payout.account.username}" if payout.account.username else payout.account.name
    await callback.message.edit_text(
        f"💰 <b>Запрос на выплату</b>\n\n"
        f"👤 {tag}\n"
        f"💵 Сумма: ${payout.amount:.2f}",
        reply_markup=payout_action_kb(payout_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_payout_approve:"))
async def callback_payout_approve(callback: CallbackQuery) -> None:
    payout_id = int(callback.data.split(":")[1])
    await payout_service.approve_payout(payout_id)
    await callback.answer("✅ Отмечено как оплачено.", show_alert=True)
    await _show_finance_page(callback.message, page=0)


@router.callback_query(F.data.startswith("admin_payout_reject:"))
async def callback_payout_reject(callback: CallbackQuery) -> None:
    payout_id = int(callback.data.split(":")[1])
    await payout_service.reject_payout(payout_id)
    await callback.answer("❌ Запрос отклонён.", show_alert=True)
    await _show_finance_page(callback.message, page=0)


# --- Question bank management ---

_ANSWER_TYPE_RU = {"text": "Текст", "number": "Число", "yes_no": "Да/Нет"}


@router.message(F.text == "❓ Вопросы")
async def cmd_questions_menu(message: Message) -> None:
    await _show_questions_list(message)


@router.callback_query(F.data == "admin_questions_menu")
async def callback_questions_menu(callback: CallbackQuery) -> None:
    questions = await job_service.list_all_questions()
    await callback.message.edit_text(
        "❓ <b>Банк вопросов</b>",
        reply_markup=questions_list_kb(questions),
    )
    await callback.answer()


async def _show_questions_list(target: Message) -> None:
    questions = await job_service.list_all_questions()
    await target.answer(
        "❓ <b>Банк вопросов</b>",
        reply_markup=questions_list_kb(questions),
    )


@router.callback_query(F.data.startswith("admin_question_detail:"))
async def callback_question_detail(callback: CallbackQuery) -> None:
    question_id = int(callback.data.split(":")[1])
    q = await job_service.get_question(question_id)
    if q is None:
        await callback.answer("Вопрос не найден.", show_alert=True)
        return
    type_ru = _ANSWER_TYPE_RU.get(q.expected_answer_type, q.expected_answer_type)
    await callback.message.edit_text(
        f"❓ <b>{q.title}</b>\n\n{q.description}\n\nТип ответа: {type_ru}",
        reply_markup=question_detail_kb(question_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_question_delete:"))
async def callback_question_delete(callback: CallbackQuery) -> None:
    question_id = int(callback.data.split(":")[1])
    await callback.message.edit_reply_markup(reply_markup=question_delete_confirm_kb(question_id))
    await callback.answer()


@router.callback_query(F.data.startswith("admin_question_delete_confirm:"))
async def callback_question_delete_confirm(callback: CallbackQuery) -> None:
    question_id = int(callback.data.split(":")[1])
    await job_service.delete_question(question_id)
    questions = await job_service.list_all_questions()
    await callback.message.edit_text(
        "✅ Вопрос удалён.\n\n❓ <b>Банк вопросов</b>",
        reply_markup=questions_list_kb(questions),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_create_question")
async def callback_create_question(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CreateQuestionStates.enter_title)
    await callback.message.edit_text("Введите короткое название вопроса (до 100 символов):")
    await callback.answer()


@router.message(CreateQuestionStates.enter_title)
async def fsm_question_title(message: Message, state: FSMContext) -> None:
    if len(message.text) > 100:
        await message.answer("Слишком длинное название, максимум 100 символов:")
        return
    await state.update_data(q_title=message.text)
    await state.set_state(CreateQuestionStates.enter_description)
    await message.answer("Введите текст вопроса (до 500 символов):")


@router.message(CreateQuestionStates.enter_description)
async def fsm_question_description(message: Message, state: FSMContext) -> None:
    if len(message.text) > 500:
        await message.answer("Слишком длинный текст, максимум 500 символов:")
        return
    await state.update_data(q_description=message.text)
    await state.set_state(CreateQuestionStates.select_answer_type)
    await message.answer("Выберите тип ответа:", reply_markup=question_answer_type_kb())


@router.callback_query(CreateQuestionStates.select_answer_type, F.data.startswith("admin_q_type:"))
async def fsm_question_answer_type(callback: CallbackQuery, state: FSMContext) -> None:
    answer_type = callback.data.split(":")[1]
    data = await state.get_data()
    await state.clear()
    q = await job_service.create_question(
        title=data["q_title"],
        description=data["q_description"],
        answer_type=answer_type,
    )
    type_ru = _ANSWER_TYPE_RU.get(answer_type, answer_type)
    questions = await job_service.list_all_questions()
    await callback.message.edit_text(
        f"✅ Вопрос <b>{q.title}</b> добавлен (тип: {type_ru}).\n\n❓ <b>Банк вопросов</b>",
        reply_markup=questions_list_kb(questions),
    )
    await callback.answer()
