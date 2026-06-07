import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.utils.logger import get_logger

logger = get_logger(__name__)


class TimingMiddleware(BaseMiddleware):
    """
    Outer middleware that measures and logs total time spent processing each update.
    Helps identify whether slowness is in handlers, DB, or Telegram API calls.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        update_type = type(event).__name__
        start = time.monotonic()
        try:
            return await handler(event, data)
        finally:
            elapsed_ms = (time.monotonic() - start) * 1000
            logger.info(
                "Update processed | type=%s elapsed_ms=%.1f",
                update_type,
                elapsed_ms,
            )
