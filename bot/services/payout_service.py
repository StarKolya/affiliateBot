from decimal import Decimal
from typing import List, Optional

from bot.models.payout import PayoutRequest
from bot.repositories.payout_repository import PayoutRepository
from bot.utils.logger import get_logger

logger = get_logger(__name__)

payout_repo = PayoutRepository()


async def request_payout(account_id: int, amount: Decimal) -> PayoutRequest:
    """
    Create a pending payout request.
    Raises ValueError if user already has a pending request.
    """
    ...


async def approve_payout(payout_id: int, admin_note: Optional[str] = None) -> PayoutRequest:
    ...


async def reject_payout(payout_id: int, admin_note: Optional[str] = None) -> PayoutRequest:
    ...


async def list_pending_payouts() -> List[PayoutRequest]:
    ...


async def list_user_payouts(account_id: int) -> List[PayoutRequest]:
    ...
