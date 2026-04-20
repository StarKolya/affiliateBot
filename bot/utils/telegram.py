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
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member.status in _SUBSCRIBED_STATUSES
    except TelegramAPIError as exc:
        logger.warning(
            "Could not check channel membership | channel=%s user=%s error=%s",
            channel_id,
            user_id,
            exc,
        )
        return False
