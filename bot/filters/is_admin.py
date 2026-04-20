from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject, User

from bot.models.account import Account


class IsAdmin(BaseFilter):
    async def __call__(self, event: TelegramObject, event_from_user: User | None = None) -> bool:
        if event_from_user is None:
            return False
        account = await Account.get_or_none(telegram_id=event_from_user.id).prefetch_related("role")
        return account is not None and account.role.name == "admin"
