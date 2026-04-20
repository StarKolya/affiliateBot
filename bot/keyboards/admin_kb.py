from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup


def admin_menu_kb() -> ReplyKeyboardMarkup:
    """Main admin panel keyboard."""
    ...


def application_status_kb(application_id: int) -> InlineKeyboardMarkup:
    """Inline buttons for each possible application status."""
    ...


def payout_action_kb(payout_id: int) -> InlineKeyboardMarkup:
    """Approve / Reject buttons for a payout request."""
    ...
