from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

JOB_TYPES = ("partnership", "offer")

# DB values — do not translate. Used in callback_data and status comparisons.
STATUSES_BY_TYPE: dict[str, tuple] = {
    "partnership": ("Pending", "Declined", "Deal Closed"),
    "offer": ("Pending", "Declined", "Joined Team", "Bought Course"),
}

_STATUS_DISPLAY_RU = {
    "Pending": "На рассмотрении",
    "Declined": "Отклонено",
    "Deal Closed": "Сделка закрыта",
    "Joined Team": "Вступил в команду",
    "Bought Course": "Купил курс",
}

_JOB_TYPE_RU = {
    "partnership": "Партнёрство",
    "offer": "Оффер",
}


def admin_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="📋 Отклики")
    builder.button(text="💼 Вакансии")
    builder.button(text="🏷 Ниши")
    builder.button(text="🔗 Рефералы")
    builder.button(text="❓ Вопросы")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def questions_list_kb(questions, page: int = 0, total_pages: int = 1) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for q in questions:
        builder.button(text=q.title, callback_data=f"admin_question_detail:{q.id}")
    nav = []
    if page > 0:
        nav.append(("◀️", f"admin_q_list_page:{page - 1}"))
    if page < total_pages - 1:
        nav.append(("▶️", f"admin_q_list_page:{page + 1}"))
    for text, cb in nav:
        builder.button(text=text, callback_data=cb)
    builder.button(text="➕ Добавить вопрос", callback_data="admin_create_question")
    rows = [1] * len(questions)
    if nav:
        rows.append(len(nav))
    rows.append(1)
    builder.adjust(*rows)
    return builder.as_markup()


def question_detail_kb(question_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Удалить", callback_data=f"admin_question_delete:{question_id}")
    builder.button(text="⬅️ Назад", callback_data="admin_questions_menu")
    builder.adjust(1)
    return builder.as_markup()


def question_delete_confirm_kb(question_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, удалить", callback_data=f"admin_question_delete_confirm:{question_id}")
    builder.button(text="❌ Отмена", callback_data=f"admin_question_detail:{question_id}")
    builder.adjust(1)
    return builder.as_markup()


def question_answer_type_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Текст", callback_data="admin_q_type:text")
    builder.button(text="Число", callback_data="admin_q_type:number")
    builder.button(text="Да/Нет", callback_data="admin_q_type:yes_no")
    builder.button(text="❌ Отмена", callback_data="admin_cancel")
    builder.adjust(3, 1)
    return builder.as_markup()


def jobs_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Создать вакансию", callback_data="admin_create_job")
    builder.button(text="📋 Управление вакансиями", callback_data="admin_manage_jobs")
    builder.adjust(1)
    return builder.as_markup()


def niches_manage_kb(niches) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for niche in niches:
        builder.button(text=niche.name, callback_data=f"admin_niche_detail:{niche.id}")
    builder.button(text="➕ Добавить нишу", callback_data="admin_create_niche")
    builder.adjust(1)
    return builder.as_markup()


def niche_detail_kb(niche_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Удалить нишу", callback_data=f"admin_niche_delete:{niche_id}")
    builder.button(text="⬅️ Назад", callback_data="admin_niches_menu")
    builder.adjust(1)
    return builder.as_markup()


def niche_delete_confirm_kb(niche_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, удалить", callback_data=f"admin_niche_delete_confirm:{niche_id}")
    builder.button(text="❌ Отмена", callback_data=f"admin_niche_detail:{niche_id}")
    builder.adjust(1)
    return builder.as_markup()


def jobs_manage_niche_kb(niches) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for niche in niches:
        builder.button(text=niche.name, callback_data=f"admin_manage_jobs_niche:{niche.id}")
    builder.button(text="⬅️ Назад", callback_data="admin_jobs_menu")
    builder.adjust(1)
    return builder.as_markup()


_STATUS_ICON = {"active": "🟢", "paused": "🟡", "closed": "🔴"}


def jobs_manage_list_kb(jobs, niche_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for job in jobs:
        icon = _STATUS_ICON.get(job.status, "⚪")
        builder.button(text=f"{icon} {job.title}", callback_data=f"admin_manage_job:{job.id}:{niche_id}")
    builder.button(text="⬅️ Назад", callback_data="admin_manage_jobs")
    builder.adjust(1)
    return builder.as_markup()


def job_manage_detail_kb(job_id: int, status: str, niche_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if status == "active":
        builder.button(text="⏸ Приостановить", callback_data=f"admin_job_toggle:{job_id}:{niche_id}")
    else:
        builder.button(text="▶️ Активировать", callback_data=f"admin_job_toggle:{job_id}:{niche_id}")
    builder.button(text="⬅️ Назад", callback_data=f"admin_manage_jobs_niche:{niche_id}")
    builder.adjust(1)
    return builder.as_markup()


def admin_niche_select_kb(niches) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for niche in niches:
        builder.button(text=niche.name, callback_data=f"admin_niche:{niche.id}")
    builder.button(text="❌ Отмена", callback_data="admin_cancel")
    builder.adjust(1)
    return builder.as_markup()


def job_type_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for job_type in JOB_TYPES:
        builder.button(text=_JOB_TYPE_RU.get(job_type, job_type.capitalize()), callback_data=f"admin_job_type:{job_type}")
    builder.button(text="❌ Отмена", callback_data="admin_cancel")
    builder.adjust(1)
    return builder.as_markup()


def skip_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭ Пропустить", callback_data="admin_skip")
    builder.adjust(1)
    return builder.as_markup()


APPS_PAGE_SIZE = 5
QUESTIONS_PAGE_SIZE = 5


def question_select_kb(
    questions, selected_ids: set, page: int, total_pages: int
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for q in questions:
        label = q.title
        if q.id in selected_ids:
            label = f"{label} +"
        builder.button(text=label, callback_data=f"admin_q_toggle:{q.id}")

    nav = []
    if page > 0:
        nav.append(("◀️", f"admin_q_page:{page - 1}"))
    if page < total_pages - 1:
        nav.append(("▶️", f"admin_q_page:{page + 1}"))
    for text, cb in nav:
        builder.button(text=text, callback_data=cb)

    builder.button(text="✅ Подтвердить", callback_data="admin_q_confirm")

    rows = [1] * len(questions)
    if nav:
        rows.append(len(nav))
    rows.append(1)
    builder.adjust(*rows)
    return builder.as_markup()


def applications_page_kb(
    apps, page: int, total_pages: int, has_filters: bool, has_sort: bool, has_status_filter: bool = False
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for app in apps:
        status_ru = _STATUS_DISPLAY_RU.get(app.status.name, app.status.name)
        label = f"{app.account.name} — {app.job_posting.title} ({status_ru})"
        builder.button(text=label, callback_data=f"admin_app:{app.id}")

    nav = []
    if page > 0:
        nav.append(("◀️ Назад", "admin_apps_prev"))
    filter_label = "🔍 Фильтры ●" if has_filters else "🔍 Фильтры"
    nav.append((filter_label, "admin_apps_filters"))
    sort_label = "↕️ Сортировка ●" if has_sort else "↕️ Сортировка"
    nav.append((sort_label, "admin_apps_sort"))
    status_label = "🏷 Статус ●" if has_status_filter else "🏷 Статус"
    nav.append((status_label, "admin_apps_status_filter"))
    if page < total_pages - 1:
        nav.append(("Вперёд ▶️", "admin_apps_next"))

    for text, cb in nav:
        builder.button(text=text, callback_data=cb)

    builder.adjust(*([1] * len(apps)), len(nav))
    return builder.as_markup()


def application_status_filter_kb(active_statuses: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for status, label in _STATUS_DISPLAY_RU.items():
        prefix = "✅ " if status in active_statuses else ""
        builder.button(text=f"{prefix}{label}", callback_data=f"admin_status_toggle:{status}")
    if active_statuses:
        builder.button(text="🗑 Сбросить", callback_data="admin_status_filter_clear")
    builder.button(text="⬅️ К откликам", callback_data="admin_apps_back")
    builder.adjust(1)
    return builder.as_markup()


def application_sort_kb(numeric_questions: list, sort_by: str | None, ascending: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    options = [("date", "По дате")]
    for q in numeric_questions:
        options.append((str(q["jq_id"]), q["text"]))

    for key, label in options:
        if sort_by == key:
            direction = "↑" if ascending else "↓"
            builder.button(text=f"✅ {direction} {label}", callback_data=f"admin_sort_toggle:{key}")
        else:
            builder.button(text=label, callback_data=f"admin_sort_set:{key}")

    if sort_by:
        builder.button(text="🗑 Сбросить сортировку", callback_data="admin_sort_clear")
    builder.button(text="⬅️ К откликам", callback_data="admin_apps_back")
    builder.adjust(1)
    return builder.as_markup()


def application_filter_kb(numeric_questions: list, active_filters: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for q in numeric_questions:
        jq_id = str(q["jq_id"])
        label = q["text"]
        if jq_id in active_filters:
            label = f"✅ {label} (мин: {active_filters[jq_id]:.0f})"
        builder.button(text=label, callback_data=f"admin_filter_set:{q['jq_id']}")
    if active_filters:
        builder.button(text="🗑 Сбросить фильтры", callback_data="admin_filter_clear")
    builder.button(text="⬅️ К откликам", callback_data="admin_apps_back")
    builder.adjust(1)
    return builder.as_markup()


def application_status_kb(application_id: int, current_status: str, job_type: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    statuses = STATUSES_BY_TYPE.get(job_type, ("Pending", "Declined"))
    for status in statuses:
        display = _STATUS_DISPLAY_RU.get(status, status)
        builder.button(text=display, callback_data=f"app_status:{application_id}:{status}")
    builder.button(text="⬅️ Назад", callback_data="admin_list_applications")
    builder.adjust(1)
    return builder.as_markup()


REFERRERS_PAGE_SIZE = 8
FINANCE_PAGE_SIZE = 8


def referrals_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Все рефереры", callback_data="admin_all_referrers")
    builder.button(text="💰 Финансы", callback_data="admin_finance")
    builder.adjust(1)
    return builder.as_markup()


def referrers_list_kb(accounts, page: int, total_pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for acc in accounts:
        label = acc.name
        if acc.username:
            label += f" (@{acc.username})"
        builder.button(text=label, callback_data=f"admin_referrer:{acc.id}")
    nav = []
    if page > 0:
        nav.append(("◀️", f"admin_referrers_page:{page - 1}"))
    if page < total_pages - 1:
        nav.append(("▶️", f"admin_referrers_page:{page + 1}"))
    for text, cb in nav:
        builder.button(text=text, callback_data=cb)
    builder.button(text="⬅️ Назад", callback_data="admin_referrals_menu")
    rows = [1] * len(accounts)
    if nav:
        rows.append(len(nav))
    rows.append(1)
    builder.adjust(*rows)
    return builder.as_markup()


def referrer_detail_kb(account_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Выплатить", callback_data=f"admin_pay_user:{account_id}")
    builder.button(text="⬅️ Назад", callback_data="admin_all_referrers")
    builder.adjust(1)
    return builder.as_markup()


def finance_list_kb(payouts, page: int, total_pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in payouts:
        tag = f"@{p.account.username}" if p.account.username else p.account.name
        builder.button(text=f"{tag} | ${p.amount:.2f}", callback_data=f"admin_payout:{p.id}")
    nav = []
    if page > 0:
        nav.append(("◀️", f"admin_finance_page:{page - 1}"))
    if page < total_pages - 1:
        nav.append(("▶️", f"admin_finance_page:{page + 1}"))
    for text, cb in nav:
        builder.button(text=text, callback_data=cb)
    builder.button(text="⬅️ Назад", callback_data="admin_referrals_menu")
    rows = [1] * len(payouts)
    if nav:
        rows.append(len(nav))
    rows.append(1)
    builder.adjust(*rows)
    return builder.as_markup()


def payout_action_kb(payout_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Оплачено", callback_data=f"admin_payout_approve:{payout_id}")
    builder.button(text="❌ Отклонить", callback_data=f"admin_payout_reject:{payout_id}")
    builder.button(text="⬅️ Назад", callback_data="admin_finance")
    builder.adjust(2, 1)
    return builder.as_markup()
