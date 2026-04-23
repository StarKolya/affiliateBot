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
    builder = InlineKeyboardBuilder()
    for niche in niches:
        builder.button(text=niche.name, callback_data=f"niche:{niche.id}")
    builder.adjust(1)
    return builder.as_markup()


def job_list_kb(jobs, niche_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for job in jobs:
        builder.button(text=job.title, callback_data=f"job:{job.id}:{niche_id}:multi")
    builder.button(text="⬅️ Back to niches", callback_data="browse_jobs")
    builder.adjust(1)
    return builder.as_markup()


def job_detail_kb(job_id: int, back_callback: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Apply", callback_data=f"apply:{job_id}")
    builder.button(text="⬅️ Back", callback_data=back_callback)
    builder.adjust(1)
    return builder.as_markup()


def referral_links_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Create New Link", callback_data="referral_create")
    builder.adjust(1)
    return builder.as_markup()
