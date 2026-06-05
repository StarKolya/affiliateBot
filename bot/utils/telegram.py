from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from bot.utils.logger import get_logger

logger = get_logger(__name__)

_SUBSCRIBED_STATUSES = {"member", "administrator", "creator"}


async def is_channel_member(bot: Bot, channel_id: int, user_id: int) -> bool:
    # TODO: remove stub before prod
    # try:
    #     member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
    #     return member.status in _SUBSCRIBED_STATUSES
    # except TelegramAPIError as exc:
    #     logger.warning("Could not check channel membership | channel=%s user=%s error=%s", channel_id, user_id, exc)
    #     return False
    return True
