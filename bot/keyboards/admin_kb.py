from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

JOB_TYPES = ("partnership", "offer")

STATUSES_BY_TYPE: dict[str, tuple] = {
    "partnership": ("Pending", "Declined", "Deal Closed"),
    "offer": ("Pending", "Declined", "Joined Team", "Bought Course"),
}


def admin_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="📋 Applications")
    builder.button(text="💼 Jobs")
    builder.button(text="🏷 Niches")
    builder.button(text="🔗 Referrals")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def jobs_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Create Job", callback_data="admin_create_job")
    builder.button(text="📋 Manage Jobs", callback_data="admin_manage_jobs")
    builder.adjust(1)
    return builder.as_markup()


def niches_manage_kb(niches) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for niche in niches:
        builder.button(text=niche.name, callback_data=f"admin_niche_detail:{niche.id}")
    builder.button(text="➕ Create Niche", callback_data="admin_create_niche")
    builder.adjust(1)
    return builder.as_markup()


def niche_detail_kb(niche_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Delete Niche", callback_data=f"admin_niche_delete:{niche_id}")
    builder.button(text="⬅️ Back", callback_data="admin_niches_menu")
    builder.adjust(1)
    return builder.as_markup()


def niche_delete_confirm_kb(niche_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Yes, delete", callback_data=f"admin_niche_delete_confirm:{niche_id}")
    builder.button(text="❌ Cancel", callback_data=f"admin_niche_detail:{niche_id}")
    builder.adjust(1)
    return builder.as_markup()


def jobs_manage_niche_kb(niches) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for niche in niches:
        builder.button(text=niche.name, callback_data=f"admin_manage_jobs_niche:{niche.id}")
    builder.button(text="⬅️ Back", callback_data="admin_jobs_menu")
    builder.adjust(1)
    return builder.as_markup()


_STATUS_ICON = {"active": "🟢", "paused": "🟡", "closed": "🔴"}


def jobs_manage_list_kb(jobs, niche_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for job in jobs:
        icon = _STATUS_ICON.get(job.status, "⚪")
        builder.button(text=f"{icon} {job.title}", callback_data=f"admin_manage_job:{job.id}:{niche_id}")
    builder.button(text="⬅️ Back", callback_data="admin_manage_jobs")
    builder.adjust(1)
    return builder.as_markup()


def job_manage_detail_kb(job_id: int, status: str, niche_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if status == "active":
        builder.button(text="⏸ Pause", callback_data=f"admin_job_toggle:{job_id}:{niche_id}")
    else:
        builder.button(text="▶️ Enable", callback_data=f"admin_job_toggle:{job_id}:{niche_id}")
    builder.button(text="⬅️ Back", callback_data=f"admin_manage_jobs_niche:{niche_id}")
    builder.adjust(1)
    return builder.as_markup()


def admin_niche_select_kb(niches) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for niche in niches:
        builder.button(text=niche.name, callback_data=f"admin_niche:{niche.id}")
    builder.button(text="❌ Cancel", callback_data="admin_cancel")
    builder.adjust(1)
    return builder.as_markup()


def job_type_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for job_type in JOB_TYPES:
        builder.button(text=job_type.capitalize(), callback_data=f"admin_job_type:{job_type}")
    builder.button(text="❌ Cancel", callback_data="admin_cancel")
    builder.adjust(1)
    return builder.as_markup()


def skip_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭ Skip", callback_data="admin_skip")
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

    builder.button(text="Confirm", callback_data="admin_q_confirm")

    rows = [1] * len(questions)
    if nav:
        rows.append(len(nav))
    rows.append(1)
    builder.adjust(*rows)
    return builder.as_markup()


def applications_page_kb(apps, page: int, total_pages: int, has_filters: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for app in apps:
        label = f"{app.account.name} — {app.job_posting.title} ({app.status.name})"
        builder.button(text=label, callback_data=f"admin_app:{app.id}")

    nav = []
    if page > 0:
        nav.append(("◀️ Prev", "admin_apps_prev"))
    filter_label = "🔍 Filters ●" if has_filters else "🔍 Filters"
    nav.append((filter_label, "admin_apps_filters"))
    if page < total_pages - 1:
        nav.append(("▶️ Next", "admin_apps_next"))

    for text, cb in nav:
        builder.button(text=text, callback_data=cb)

    builder.button(text="📥 Export CSV", callback_data="admin_apps_export")
    builder.adjust(*([1] * len(apps)), len(nav), 1)
    return builder.as_markup()


def application_filter_kb(numeric_questions: list, active_filters: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for q in numeric_questions:
        jq_id = str(q["jq_id"])
        label = q["text"]
        if jq_id in active_filters:
            label = f"✅ {label} (min: {active_filters[jq_id]:.0f})"
        builder.button(text=label, callback_data=f"admin_filter_set:{q['jq_id']}")
    if active_filters:
        builder.button(text="🗑 Clear all filters", callback_data="admin_filter_clear")
    builder.button(text="⬅️ Back to applications", callback_data="admin_apps_back")
    builder.adjust(1)
    return builder.as_markup()


def application_status_kb(application_id: int, current_status: str, job_type: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    statuses = STATUSES_BY_TYPE.get(job_type, ("Pending", "Declined"))
    for status in statuses:
        if status == current_status:
            builder.button(text=f"✅ {status}", callback_data="app_status_noop")
        else:
            builder.button(text=status, callback_data=f"app_status:{application_id}:{status}")
    builder.button(text="⬅️ Back", callback_data="admin_list_applications")
    builder.adjust(1)
    return builder.as_markup()


REFERRERS_PAGE_SIZE = 8
FINANCE_PAGE_SIZE = 8


def referrals_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 All Referrers", callback_data="admin_all_referrers")
    builder.button(text="💰 Finance", callback_data="admin_finance")
    builder.adjust(2)
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
    builder.button(text="⬅️ Back", callback_data="admin_referrals_menu")
    rows = [1] * len(accounts)
    if nav:
        rows.append(len(nav))
    rows.append(1)
    builder.adjust(*rows)
    return builder.as_markup()


def referrer_detail_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Back", callback_data="admin_all_referrers")
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
    builder.button(text="⬅️ Back", callback_data="admin_referrals_menu")
    rows = [1] * len(payouts)
    if nav:
        rows.append(len(nav))
    rows.append(1)
    builder.adjust(*rows)
    return builder.as_markup()


def payout_action_kb(payout_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Paid", callback_data=f"admin_payout_approve:{payout_id}")
    builder.button(text="❌ Rejected", callback_data=f"admin_payout_reject:{payout_id}")
    builder.button(text="⬅️ Back", callback_data="admin_finance")
    builder.adjust(2, 1)
    return builder.as_markup()
