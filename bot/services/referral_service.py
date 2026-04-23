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

# Maps job_type → {status_name: commission_field}
# "primary" = job.commission, "secondary" = job.commission_secondary
EARNING_TRIGGERS: dict[str, dict[str, str]] = {
    "partnership": {
        "Deal Closed": "primary",
    },
    "offer": {
        "Joined Team": "primary",
        "Bought Course": "secondary",
    },
}

STATUSES_PENDING = ("Pending",)
STATUSES_DECLINED = ("Declined",)
STATUSES_ACCEPTED = ("Deal Closed", "Joined Team", "Bought Course")


@dataclass
class ReferralStats:
    referral: Referral
    referred_users: int
    applications: int
    pending: int
    declined: int
    accepted: int
    earned: Decimal


@dataclass
class AccountReferralStats:
    total_referred: int
    total_applications: int
    total_pending: int
    total_declined: int
    total_accepted: int
    total_earned: Decimal


async def create_referral_link(account_id: int, name: str) -> Referral:
    """Auto-generates a unique code and creates the referral link."""
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
    base = JobApplication.filter(referral__account_id=account_id)
    total_applications = await base.count()
    total_pending = await base.filter(status__name__in=STATUSES_PENDING).count()
    total_declined = await base.filter(status__name__in=STATUSES_DECLINED).count()
    total_accepted = await base.filter(status__name__in=STATUSES_ACCEPTED).count()
    total_earned = await earning_repo.get_total_earned(account_id)
    return AccountReferralStats(
        total_referred=total_referred,
        total_applications=total_applications,
        total_pending=total_pending,
        total_declined=total_declined,
        total_accepted=total_accepted,
        total_earned=total_earned,
    )


async def get_referral_stats(referral: Referral) -> ReferralStats:
    referred_users = await Account.filter(referred_by_code=referral.code).count()
    base = JobApplication.filter(referral_id=referral.id)
    applications = await base.count()
    pending = await base.filter(status__name__in=STATUSES_PENDING).count()
    declined = await base.filter(status__name__in=STATUSES_DECLINED).count()
    accepted = await base.filter(status__name__in=STATUSES_ACCEPTED).count()
    earned = await earning_repo.get_earned_by_referral(referral.id)
    return ReferralStats(
        referral=referral,
        referred_users=referred_users,
        applications=applications,
        pending=pending,
        declined=declined,
        accepted=accepted,
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
    """
    Idempotent: creates a ReferralEarning only when the new status is a
    trigger for the given job type. Amount depends on which trigger fired.
    DB unique_together on ReferralEarning is the second idempotency guard.
    """
    triggers = EARNING_TRIGGERS.get(job_type, {})
    commission_field = triggers.get(new_status_name)
    if commission_field is None:
        return None

    amount = commission if commission_field == "primary" else (commission_secondary or Decimal("0"))
    if amount <= 0:
        return None

    already = await earning_repo.earning_exists(referral_id, application_id)
    if already:
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
