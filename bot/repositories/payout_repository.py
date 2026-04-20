from typing import List, Optional

from bot.models.payout import PayoutRequest
from bot.repositories.base import BaseRepository


class PayoutRepository(BaseRepository[PayoutRequest]):
    model = PayoutRequest

    async def get_by_account(self, account_id: int) -> List[PayoutRequest]:
        return await PayoutRequest.filter(account_id=account_id).order_by("-created_at")

    async def get_pending(self) -> List[PayoutRequest]:
        return await PayoutRequest.filter(status="pending").prefetch_related("account")

    async def has_pending(self, account_id: int) -> bool:
        return await PayoutRequest.filter(account_id=account_id, status="pending").exists()
