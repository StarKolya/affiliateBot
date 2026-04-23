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
    builder.button(text="💰 Payouts")
    builder.button(text="💼 Jobs")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def jobs_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Create Job", callback_data="admin_create_job")
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

    builder.adjust(*([1] * len(apps)), len(nav))
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


def payout_action_kb(payout_id: int) -> InlineKeyboardMarkup:
    """Approve / Reject buttons for a payout request."""
    ...
