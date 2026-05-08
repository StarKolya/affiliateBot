import time
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, Bot
from aiogram.types import CallbackQuery, FSInputFile, Message, TelegramObject

from bot.config import settings
from bot.keyboards.user_kb import subscription_check_kb
from bot.utils.logger import get_logger
from bot.utils.telegram import is_subscribed_to_all

logger = get_logger(__name__)

_SUBSCRIBE_IMAGE = Path(__file__).parent.parent / "images" / "start.jpg"

# How long (seconds) to trust a positive membership result before re-checking.
_CACHE_TTL = 300  # 5 minutes

# {telegram_id: (is_member: bool, checked_at: float)}
_cache: dict[int, tuple[bool, float]] = {}


def _cached_result(user_id: int) -> bool | None:
    entry = _cache.get(user_id)
    if entry and (time.monotonic() - entry[1]) < _CACHE_TTL:
        return entry[0]
    return None


def _set_cache(user_id: int, value: bool) -> None:
    _cache[user_id] = (value, time.monotonic())


def _channel_ids() -> list[int]:
    ids = [settings.CHANNEL_ID]
    if settings.CHANNEL_ID_2:
        ids.append(settings.CHANNEL_ID_2)
    return ids


_SUBSCRIBE_CAPTION = (
    "Для использования бота необходимо подписаться на наш канал и вступить в группу.\n"
    "Подпишись и нажми кнопку ниже."
)

# Updates that drive the subscription flow itself — let them through unconditionally.
_EXEMPT_CALLBACKS = {"check_subscription"}


class SubscriptionMiddleware(BaseMiddleware):
    """
    Blocks every message/callback from users who are not subscribed to all
    configured channels.  Membership is re-checked every _CACHE_TTL seconds so
    a user who unsubscribes will be blocked on their next interaction after the
    TTL expires.

    Exemptions:
      - /start  (handles its own subscription prompt for new users)
      - check_subscription callback  (the "I subscribed" button handler)
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        bot: Bot = data["bot"]

        if isinstance(event, Message):
            user = event.from_user
            # Let /start through — it manages its own flow
            if event.text and event.text.startswith("/start"):
                return await handler(event, data)

        elif isinstance(event, CallbackQuery):
            user = event.from_user
            if event.data in _EXEMPT_CALLBACKS:
                return await handler(event, data)
        else:
            return await handler(event, data)

        if user is None:
            return await handler(event, data)

        # Check cache first
        cached = _cached_result(user.id)
        if cached is True:
            return await handler(event, data)

        is_member = await is_subscribed_to_all(bot, _channel_ids(), user.id)
        _set_cache(user.id, is_member)

        if is_member:
            return await handler(event, data)

        # User is not subscribed — block and prompt
        logger.info("Blocked unsubscribed user | telegram_id=%s", user.id)

        kb = subscription_check_kb(settings.CHANNEL_URL, settings.CHANNEL_URL_2)

        if isinstance(event, Message):
            await event.answer_photo(
                FSInputFile(_SUBSCRIBE_IMAGE),
                caption=_SUBSCRIBE_CAPTION,
                reply_markup=kb,
            )
        elif isinstance(event, CallbackQuery):
            await event.answer(
                "Ты отписался. Подпишись снова, чтобы продолжить.",
                show_alert=True,
            )
            # Also send the photo prompt so the user sees the buttons
            await event.message.answer_photo(
                FSInputFile(_SUBSCRIBE_IMAGE),
                caption=_SUBSCRIBE_CAPTION,
                reply_markup=kb,
            )
