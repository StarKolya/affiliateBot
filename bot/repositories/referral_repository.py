from decimal import Decimal
from typing import List, Optional

from bot.models.referral import Referral, ReferralEarning
from bot.repositories.base import BaseRepository


class ReferralRepository(BaseRepository[Referral]):
    model = Referral

    async def get_by_code(self, code: str) -> Optional[Referral]:
        return await Referral.get_or_none(code=code)

    async def get_by_account(self, account_id: int) -> List[Referral]:
        return await Referral.filter(account_id=account_id)

    async def code_exists(self, code: str) -> bool:
        return await Referral.filter(code=code).exists()


class ReferralEarningRepository(BaseRepository[ReferralEarning]):
    model = ReferralEarning

    async def get_by_referral(self, referral_id: int) -> List[ReferralEarning]:
        return await ReferralEarning.filter(referral_id=referral_id)

    async def earning_exists(self, referral_id: int, application_id: int) -> bool:
        return await ReferralEarning.filter(
            referral_id=referral_id, application_id=application_id
        ).exists()

    async def get_total_earned(self, account_id: int) -> Decimal:
        result = await ReferralEarning.filter(
            referral__account_id=account_id
        ).values("amount")
        return sum((r["amount"] for r in result), Decimal("0.00"))

    async def get_earned_by_referral(self, referral_id: int) -> Decimal:
        result = await ReferralEarning.filter(referral_id=referral_id).values("amount")
        return sum((r["amount"] for r in result), Decimal("0.00"))
