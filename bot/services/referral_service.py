import secrets
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional

from bot.models.application import JobApplication
from bot.models.account import Account
from bot.models.referral import Referral, ReferralEarning
from bot.repositories.referral_repository import ReferralEarningRepository, ReferralRepository
from bot.utils.logger import get_logger

logger = get_logger(__name__)

referral_repo = ReferralRepository()
earning_repo = ReferralEarningRepository()

EARNING_TRIGGERS: dict[str, dict[str, str]] = {
    "partnership": {
        "Deal Closed": "primary",
    },
    "offer": {
        "Joined Team": "primary",
        "Bought Course": "secondary",
    },
}

@dataclass
class ReferralStats:
    referral: Referral
    referred_users: int
    applications: int
    pending: int
    declined: int
    deal_closed: int
    joined_team: int
    bought_course: int
    earned: Decimal


@dataclass
class AccountReferralStats:
    total_referred: int
    total_applications: int
    total_pending: int
    total_declined: int
    total_deal_closed: int
    total_joined_team: int
    total_bought_course: int
    total_earned: Decimal


async def create_referral_link(account_id: int, name: str) -> Referral:
    for _ in range(5):
        code = secrets.token_urlsafe(8)
        if not await referral_repo.code_exists(code):
            return await referral_repo.create(account_id=account_id, name=name, code=code)
    raise RuntimeError("Failed to generate a unique referral code after 5 attempts")


async def get_referral_by_code(code: str) -> Optional[Referral]:
    return await referral_repo.get_by_code(code)


async def list_user_referrals(account_id: int) -> List[Referral]:
    return await referral_repo.get_by_account(account_id)


async def get_account_stats(account_id: int) -> AccountReferralStats:
    referrals = await referral_repo.get_by_account(account_id)
    codes = [r.code for r in referrals]
    total_referred = await Account.filter(referred_by_code__in=codes).count() if codes else 0
    qs = JobApplication.filter(referral__account_id=account_id)
    total_applications = await qs.count()
    total_pending = await qs.filter(status__name="Pending").count()
    total_declined = await qs.filter(status__name="Declined").count()
    total_deal_closed = await qs.filter(status__name="Deal Closed").count()
    total_joined_team = await qs.filter(status__name="Joined Team").count()
    total_bought_course = await qs.filter(status__name="Bought Course").count()
    total_earned = await earning_repo.get_total_earned(account_id)
    return AccountReferralStats(
        total_referred=total_referred,
        total_applications=total_applications,
        total_pending=total_pending,
        total_declined=total_declined,
        total_deal_closed=total_deal_closed,
        total_joined_team=total_joined_team,
        total_bought_course=total_bought_course,
        total_earned=total_earned,
    )


async def get_referral_stats(referral: Referral) -> ReferralStats:
    referred_users = await Account.filter(referred_by_code=referral.code).count()
    qs = JobApplication.filter(referral_id=referral.id)
    applications = await qs.count()
    pending = await qs.filter(status__name="Pending").count()
    declined = await qs.filter(status__name="Declined").count()
    deal_closed = await qs.filter(status__name="Deal Closed").count()
    joined_team = await qs.filter(status__name="Joined Team").count()
    bought_course = await qs.filter(status__name="Bought Course").count()
    earned = await earning_repo.get_earned_by_referral(referral.id)
    return ReferralStats(
        referral=referral,
        referred_users=referred_users,
        applications=applications,
        pending=pending,
        declined=declined,
        deal_closed=deal_closed,
        joined_team=joined_team,
        bought_course=bought_course,
        earned=earned,
    )


async def maybe_create_earning(
    application_id: int,
    referral_id: int,
    new_status_name: str,
    job_type: str,
    commission: Decimal,
    commission_secondary: Optional[Decimal] = None,
) -> Optional[ReferralEarning]:
    triggers = EARNING_TRIGGERS.get(job_type, {})
    commission_field = triggers.get(new_status_name)
    if commission_field is None:
        return None

    amount = commission if commission_field == "primary" else (commission_secondary or Decimal("0"))
    if amount <= 0:
        return None

    if await earning_repo.earning_exists(referral_id, application_id):
        return None

    earning = await earning_repo.create(
        referral_id=referral_id,
        application_id=application_id,
        amount=amount,
    )
    logger.info(
        "Referral earning created | referral=%s application=%s status=%s amount=%s",
        referral_id, application_id, new_status_name, amount,
    )
    return earning


async def get_total_earned(account_id: int) -> Decimal:
    return await earning_repo.get_total_earned(account_id)


async def get_admin_overview() -> dict:
    from bot.models.payout import PayoutRequest
    total_referrers = await Referral.all().distinct().values_list("account_id", flat=True)
    total_referrers_count = len(set(total_referrers))
    total_referred = await Account.filter(referred_by_code__isnull=False).count()
    total_applications = await JobApplication.filter(referral_id__isnull=False).count()
    all_earnings = await ReferralEarning.all().values("amount")
    total_earned = sum((r["amount"] for r in all_earnings), Decimal("0.00"))
    pending_payouts = await PayoutRequest.filter(status="pending").values("amount")
    pending_payout_amount = sum((r["amount"] for r in pending_payouts), Decimal("0.00"))
    pending_payout_count = len(pending_payouts)
    return {
        "total_referrers": total_referrers_count,
        "total_referred": total_referred,
        "total_applications": total_applications,
        "total_earned": total_earned,
        "pending_payout_count": pending_payout_count,
        "pending_payout_amount": pending_payout_amount,
    }
