from typing import Optional

from bot.models.account import Account, Role
from bot.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    model = Role

    async def get_by_name(self, name: str) -> Optional[Role]:
        return await Role.get_or_none(name=name)


class UserRepository(BaseRepository[Account]):
    model = Account

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[Account]:
        return await Account.get_or_none(telegram_id=telegram_id)

    async def exists_by_telegram_id(self, telegram_id: int) -> bool:
        return await Account.filter(telegram_id=telegram_id).exists()

    async def create_user(
        self,
        telegram_id: int,
        name: str,
        surname: Optional[str],
        username: Optional[str],
        role: Role,
        referred_by_code: Optional[str],
    ) -> Account:
        return await Account.create(
            telegram_id=telegram_id,
            name=name,
            surname=surname,
            username=username,
            role=role,
            referred_by_code=referred_by_code,
            subscription_verified=False,
        )
