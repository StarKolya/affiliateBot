from typing import Optional

from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def subscription_check_kb(channel_url: Optional[str] = None) -> InlineKeyboardMarkup:
    """
    Shown to new users who are not yet subscribed.
    Optionally includes a direct channel link if CHANNEL_URL is configured.
    """
    builder = InlineKeyboardBuilder()
    if channel_url:
        builder.button(text="📢 Subscribe to channel", url=channel_url)
    builder.button(text="✅ I subscribed", callback_data="check_subscription")
    builder.adjust(1)
    return builder.as_markup()


def main_menu_kb() -> ReplyKeyboardMarkup:
    """Persistent bottom keyboard shown after a user passes the subscription check."""
    builder = ReplyKeyboardBuilder()
    builder.button(text="📋 Browse Jobs")
    builder.button(text="📊 My Applications")
    builder.button(text="🔗 Referral Links")
    builder.button(text="💰 Request Payout")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def niche_list_kb(niches) -> InlineKeyboardMarkup:
    """Inline keyboard listing available niches."""
    ...


def job_list_kb(jobs) -> InlineKeyboardMarkup:
    """Inline keyboard listing active job postings for a niche."""
    ...
