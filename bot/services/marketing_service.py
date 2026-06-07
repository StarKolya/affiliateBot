import asyncio
import json
from datetime import datetime, timezone
from typing import List, Optional

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError, TelegramBadRequest
from aiogram.types import Message, MessageEntity

from bot.models.account import Account
from bot.models.marketing import MarketingMessage
from bot.utils.logger import get_logger

logger = get_logger(__name__)

_SUPPORTED_TYPES = ("text", "photo", "video", "animation", "sticker", "document", "audio", "voice")


def extract_from_message(message: Message) -> Optional[dict]:
    """
    Extract storable content from a Telegram message.
    Returns a dict ready to be passed to MarketingMessage.create(), or None if unsupported.
    """
    content_type = message.content_type.value  # aiogram ContentType enum → string

    def _encode_entities(entities) -> Optional[str]:
        if not entities:
            return None
        return json.dumps([e.model_dump() for e in entities])

    if content_type == "text":
        return {
            "content_type": "text",
            "file_id": None,
            "text": message.text,
            "entities_json": _encode_entities(message.entities),
        }
    if content_type == "photo":
        return {
            "content_type": "photo",
            "file_id": message.photo[-1].file_id,
            "text": message.caption,
            "entities_json": _encode_entities(message.caption_entities),
        }
    if content_type == "video":
        return {
            "content_type": "video",
            "file_id": message.video.file_id,
            "text": message.caption,
            "entities_json": _encode_entities(message.caption_entities),
        }
    if content_type == "animation":
        return {
            "content_type": "animation",
            "file_id": message.animation.file_id,
            "text": message.caption,
            "entities_json": _encode_entities(message.caption_entities),
        }
    if content_type == "sticker":
        return {
            "content_type": "sticker",
            "file_id": message.sticker.file_id,
            "text": None,
            "entities_json": None,
        }
    if content_type == "document":
        return {
            "content_type": "document",
            "file_id": message.document.file_id,
            "text": message.caption,
            "entities_json": _encode_entities(message.caption_entities),
        }
    if content_type == "audio":
        return {
            "content_type": "audio",
            "file_id": message.audio.file_id,
            "text": message.caption,
            "entities_json": _encode_entities(message.caption_entities),
        }
    if content_type == "voice":
        return {
            "content_type": "voice",
            "file_id": message.voice.file_id,
            "text": message.caption,
            "entities_json": _encode_entities(message.caption_entities),
        }
    return None


def _decode_entities(entities_json: Optional[str]) -> Optional[List[MessageEntity]]:
    if not entities_json:
        return None
    raw = json.loads(entities_json)
    return [MessageEntity.model_validate(e) for e in raw]


async def _send_to_user(bot: Bot, telegram_id: int, msg: MarketingMessage) -> bool:
    entities = _decode_entities(msg.entities_json)
    try:
        ct = msg.content_type
        if ct == "text":
            await bot.send_message(telegram_id, msg.text, entities=entities)
        elif ct == "photo":
            await bot.send_photo(telegram_id, msg.file_id, caption=msg.text, caption_entities=entities)
        elif ct == "video":
            await bot.send_video(telegram_id, msg.file_id, caption=msg.text, caption_entities=entities)
        elif ct == "animation":
            await bot.send_animation(telegram_id, msg.file_id, caption=msg.text, caption_entities=entities)
        elif ct == "sticker":
            await bot.send_sticker(telegram_id, msg.file_id)
        elif ct == "document":
            await bot.send_document(telegram_id, msg.file_id, caption=msg.text, caption_entities=entities)
        elif ct == "audio":
            await bot.send_audio(telegram_id, msg.file_id, caption=msg.text, caption_entities=entities)
        elif ct == "voice":
            await bot.send_voice(telegram_id, msg.file_id, caption=msg.text, caption_entities=entities)
        return True
    except (TelegramForbiddenError, TelegramBadRequest):
        # User blocked the bot or deleted their account — skip silently
        return False
    except TelegramAPIError as e:
        logger.warning("Broadcast send failed for telegram_id=%s: %s", telegram_id, e)
        return False


async def broadcast(bot: Bot, msg: MarketingMessage, status_callback=None) -> int:
    """
    Send msg to all accounts. Returns number of successful deliveries.
    status_callback(sent, total) is called periodically so the caller can update a progress message.
    """
    accounts = await Account.all().only("telegram_id")
    total = len(accounts)
    sent = 0

    for i, account in enumerate(accounts):
        ok = await _send_to_user(bot, account.telegram_id, msg)
        if ok:
            sent += 1
        # Telegram allows ~30 msgs/sec; 20/sec keeps us safe
        await asyncio.sleep(0.05)
        # Report progress every 50 users
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
