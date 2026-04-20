from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

JOB_TYPES = ("full-time", "part-time", "contract")


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


APPLICATION_STATUSES = ("Processing", "Not accepted", "Bought training", "Joined team")


def application_status_kb(application_id: int, current_status: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for status in APPLICATION_STATUSES:
        if status == current_status:
            builder.button(text=f"✅ {status}", callback_data=f"app_status_noop")
        else:
            builder.button(text=status, callback_data=f"app_status:{application_id}:{status}")
    builder.button(text="⬅️ Back", callback_data="admin_list_applications")
    builder.adjust(1)
    return builder.as_markup()


def payout_action_kb(payout_id: int) -> InlineKeyboardMarkup:
    """Approve / Reject buttons for a payout request."""
    ...
