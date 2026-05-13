from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional

from bot.models.payout import PayoutRequest
from bot.repositories.payout_repository import PayoutRepository
from bot.services.referral_service import get_total_earned
from bot.utils.logger import get_logger

logger = get_logger(__name__)

payout_repo = PayoutRepository()


@dataclass
class PayoutSummary:
    pending_amount: Decimal
    paid_out_amount: Decimal
    available_amount: Decimal


async def get_user_summary(account_id: int) -> PayoutSummary:
    payouts = await payout_repo.get_by_account(account_id)
    pending_amount = sum(
        (p.amount for p in payouts if p.status == "pending"), Decimal("0.00")
    )
    paid_out_amount = sum(
        (p.amount for p in payouts if p.status == "approved"), Decimal("0.00")
    )
    total_earned = await get_total_earned(account_id)
    available_amount = max(Decimal("0.00"), total_earned - paid_out_amount - pending_amount)
    return PayoutSummary(
        pending_amount=pending_amount,
        paid_out_amount=paid_out_amount,
        available_amount=available_amount,
    )


async def request_payout(account_id: int, amount: Decimal) -> PayoutRequest:
    if amount <= 0:
        raise ValueError("Amount must be greater than zero")
    if await payout_repo.has_pending(account_id):
        raise ValueError("You already have a pending payout request")
    payout = await payout_repo.create(account_id=account_id, amount=amount)
    logger.info("Payout request created | account=%s amount=%s", account_id, amount)
    return payout


async def approve_payout(payout_id: int, admin_note: Optional[str] = None) -> PayoutRequest:
    payout = await PayoutRequest.get(id=payout_id)
    payout.status = "approved"
    payout.admin_note = admin_note
    await payout.save(update_fields=["status", "admin_note", "updated_at"])
    logger.info("Payout approved | id=%s", payout_id)
    return payout


async def reject_payout(payout_id: int, admin_note: Optional[str] = None) -> PayoutRequest:
    payout = await PayoutRequest.get(id=payout_id)
    payout.status = "rejected"
    payout.admin_note = admin_note
    await payout.save(update_fields=["status", "admin_note", "updated_at"])
    logger.info("Payout rejected | id=%s", payout_id)
    return payout


async def list_pending_payouts() -> List[PayoutRequest]:
    return await payout_repo.get_pending()


async def list_user_payouts(account_id: int) -> List[PayoutRequest]:
    return await payout_repo.get_by_account(account_id)


async def admin_pay_account(account_id: int, amount: Decimal) -> PayoutRequest:
    if amount <= 0:
        raise ValueError("Amount must be greater than zero")
    payout = await payout_repo.create(account_id=account_id, amount=amount)
    payout.status = "approved"
    await payout.save(update_fields=["status", "updated_at"])
    logger.info("Admin payout created | account=%s amount=%s", account_id, amount)
    return payout
