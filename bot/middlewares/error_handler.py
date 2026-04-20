from typing import Any, Awaitable, Callable, Dict, cast

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from bot.utils.logger import get_logger

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseMiddleware):
    """
    Outermost middleware registered on dp.update. Catches all unhandled
    exceptions, logs them with context, and sends a generic error reply so
    the conversation does not silently die.
    When registered on dp.update, aiogram 3 passes the Update as `event` directly.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as exc:
            update = cast(Update, event)
            user_id = None
            if update.message and update.message.from_user:
                user_id = update.message.from_user.id
            elif update.callback_query and update.callback_query.from_user:
                user_id = update.callback_query.from_user.id

            logger.exception(
                "Unhandled exception | user_id=%s | update_id=%s",
                user_id,
                update.update_id,
                exc_info=exc,
            )

            # Best-effort reply – ignore secondary failures
            try:
                if update.message:
                    await update.message.answer("An error occurred. Please try again later.")
                elif update.callback_query:
                    await update.callback_query.answer("An error occurred.", show_alert=True)
            except Exception:
                pass
