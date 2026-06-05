from decimal import Decimal
from typing import Optional

from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def subscription_check_kb(channel_url: Optional[str] = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if channel_url:
        builder.button(text="📢 Subscribe to channel", url=channel_url)
    builder.button(text="✅ I subscribed", callback_data="check_subscription")
    builder.adjust(1)
    return builder.as_markup()


def main_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="📋 Browse Jobs")
    builder.button(text="🔗 Referral Links")
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


REFERRAL_PAGE_SIZE = 5


def referral_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Stats", callback_data="referral_stats")
    builder.button(text="🔗 My Links", callback_data="referral_links")
    builder.adjust(2)
    return builder.as_markup()


def referral_stats_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 Request Payout", callback_data="payout_menu")
    builder.button(text="⬅️ Back", callback_data="referral_menu")
    builder.adjust(1)
    return builder.as_markup()


def referral_links_list_kb(links, page: int, total_pages: int, counts: dict | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Create New Link", callback_data="referral_create")
    for link in links:
        count = (counts or {}).get(link.id, 0)
        builder.button(text=f"{link.name} | applications: {count}", callback_data=f"referral_detail:{link.id}")
    nav = []
    if page > 0:
        nav.append(("◀️", f"referral_page:{page - 1}"))
    if page < total_pages - 1:
        nav.append(("▶️", f"referral_page:{page + 1}"))
    for text, cb in nav:
        builder.button(text=text, callback_data=cb)
    builder.button(text="⬅️ Back", callback_data="referral_menu")
    row_sizes = [1] + [1] * len(links)
    if nav:
        row_sizes.append(len(nav))
    row_sizes.append(1)
    builder.adjust(*row_sizes)
    return builder.as_markup()


def referral_detail_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Back to links", callback_data="referral_links")
    builder.adjust(1)
    return builder.as_markup()


def payout_menu_kb(has_available: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_available:
        builder.button(text="➕ Create Request", callback_data="payout_create")
    builder.button(text="📋 History", callback_data="payout_history")
    builder.adjust(1)
    return builder.as_markup()


PAYOUT_HISTORY_PAGE_SIZE = 5


def payout_history_kb(payouts, page: int, total_pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    nav = []
    if page > 0:
        nav.append(("◀️", f"payout_history_page:{page - 1}"))
    if page < total_pages - 1:
        nav.append(("▶️", f"payout_history_page:{page + 1}"))
    for text, cb in nav:
        builder.button(text=text, callback_data=cb)
    builder.button(text="⬅️ Back", callback_data="payout_menu")
    row_sizes = []
    if nav:
        row_sizes.append(len(nav))
    row_sizes.append(1)
    builder.adjust(*row_sizes)
    return builder.as_markup()


def payout_create_kb(available_amount) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"💰 All available (${available_amount:.2f})",
        callback_data="payout_all_available",
    )
    builder.button(text="❌ Cancel", callback_data="payout_menu")
    builder.adjust(1)
    return builder.as_markup()
