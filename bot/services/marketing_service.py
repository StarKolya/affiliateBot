import asyncio
from datetime import datetime, timezone
from typing import List, Optional

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError, TelegramBadRequest
from aiogram.types import Message

from bot.models.account import Account
from bot.models.marketing import MarketingMessage
from bot.utils.logger import get_logger

logger = get_logger(__name__)


def extract_from_message(message: Message) -> Optional[dict]:
    """
    Extract storable content from a Telegram message.
    Returns a dict ready for MarketingMessage.create(), or None if unsupported.
    """
    content_type = message.content_type.value

    supported = ("text", "photo", "video", "animation", "sticker", "document", "audio", "voice")
    if content_type not in supported:
        return None

    # Plain text/caption for preview only — actual formatting comes from copy_message
    text = message.text or message.caption

    return {
        "content_type": content_type,
        "source_chat_id": message.chat.id,
        "source_message_id": message.message_id,
        "text": text,
    }


async def _send_to_user(bot: Bot, telegram_id: int, msg: MarketingMessage) -> bool:
    try:
        await bot.copy_message(
            chat_id=telegram_id,
            from_chat_id=msg.source_chat_id,
            message_id=msg.source_message_id,
        )
        return True
    except (TelegramForbiddenError, TelegramBadRequest):
        return False
    except TelegramAPIError as e:
        logger.warning("Broadcast send failed for telegram_id=%s: %s", telegram_id, e)
        return False


async def broadcast(bot: Bot, msg: MarketingMessage, status_callback=None) -> int:
    """
    Send msg to all accounts via copy_message. Returns number of successful deliveries.
    status_callback(sent, total) is called every 50 users.
    """
    accounts = await Account.all().only("telegram_id")
    total = len(accounts)
    sent = 0

    for i, account in enumerate(accounts):
        ok = await _send_to_user(bot, account.telegram_id, msg)
        if ok:
            sent += 1
        await asyncio.sleep(0.05)
        if status_callback and (i + 1) % 50 == 0:
            await status_callback(sent, total)

    msg.sent_at = datetime.now(timezone.utc)
    msg.sent_count = sent
    await msg.save(update_fields=["sent_at", "sent_count"])

    logger.info("Broadcast id=%s complete: %s/%s delivered", msg.id, sent, total)
    return sent


async def list_recent(limit: int = 10) -> List[MarketingMessage]:
    return await MarketingMessage.all().order_by("-created_at").limit(limit)


async def get_by_id(msg_id: int) -> Optional[MarketingMessage]:
    return await MarketingMessage.get_or_none(id=msg_id)
