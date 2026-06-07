import time

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from bot.utils.logger import get_logger

logger = get_logger(__name__)

_SUBSCRIBED_STATUSES = {"member", "administrator", "creator"}


async def is_channel_member(bot: Bot, channel_id: int, user_id: int) -> bool:
    """
    Returns True if the user is an active member of the channel.
    Returns False on API errors (e.g. bot not in channel) so the caller
    can safely treat the check as failed without crashing.
    """
    start = time.monotonic()
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        result = member.status in _SUBSCRIBED_STATUSES
        elapsed_ms = (time.monotonic() - start) * 1000
        logger.info(
            "Telegram getChatMember | channel=%s user=%s result=%s elapsed_ms=%.1f",
            channel_id,
            user_id,
            result,
            elapsed_ms,
        )
        return result
    except TelegramAPIError as exc:
        elapsed_ms = (time.monotonic() - start) * 1000
        logger.warning(
            "Could not check channel membership | channel=%s user=%s error=%s elapsed_ms=%.1f",
            channel_id,
            user_id,
            exc,
            elapsed_ms,
        )
        return False


async def is_subscribed_to_all(bot: Bot, channel_ids: list[int], user_id: int) -> bool:
    """Returns True only if the user is a member of every channel in the list."""
    for channel_id in channel_ids:
        if not await is_channel_member(bot, channel_id, user_id):
            return False
    return True
