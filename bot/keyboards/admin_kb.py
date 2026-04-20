from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def admin_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="📋 Applications")
    builder.button(text="💰 Payouts")
    builder.button(text="💼 Jobs")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def application_status_kb(application_id: int) -> InlineKeyboardMarkup:
    """Inline buttons for each possible application status."""
    ...


def payout_action_kb(payout_id: int) -> InlineKeyboardMarkup:
    """Approve / Reject buttons for a payout request."""
    ...
