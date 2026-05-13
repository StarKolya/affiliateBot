from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject, User

from bot.models.account import Account
from bot.utils.logger import get_logger

logger = get_logger(__name__)

ADMIN_ROLES = {"superadmin", "admin", "admin_refs", "admin_apps"}


class IsAdmin(BaseFilter):
    async def __call__(self, event: TelegramObject, event_from_user: User | None = None) -> bool:
        if event_from_user is None:
            logger.debug("IsAdmin: no user on event")
            return False
        account = await Account.get_or_none(telegram_id=event_from_user.id).prefetch_related("role")
        if account is None:
            logger.debug("IsAdmin: no account for telegram_id=%s", event_from_user.id)
            return False
        result = account.role.name in ADMIN_ROLES
        logger.debug("IsAdmin: telegram_id=%s role=%s result=%s", event_from_user.id, account.role.name, result)
        return result
