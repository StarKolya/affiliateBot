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

# Status names that trigger a referral earning when an application reaches them
EARNING_TRIGGER_STATUSES = {"Bought training"}


@dataclass
class ReferralStats:
    referral: Referral
    referred_users: int
    applications: int
    earned: Decimal


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


async def get_referral_stats(referral: Referral) -> ReferralStats:
    referred_users = await Account.filter(referred_by_code=referral.code).count()
    applications = await JobApplication.filter(referral_id=referral.id).count()
    earned = await earning_repo.get_earned_by_referral(referral.id)
    return ReferralStats(
        referral=referral,
        referred_users=referred_users,
        applications=applications,
        earned=earned,
    )


async def maybe_create_earning(
    application_id: int,
    referral_id: int,
    new_status_name: str,
    commission: Decimal,
) -> Optional[ReferralEarning]:
    """
    Idempotent: creates a ReferralEarning only when:
      - new_status_name is in EARNING_TRIGGER_STATUSES
      - no earning already exists for this (referral, application) pair
    The DB unique_together on ReferralEarning provides a second safety net.
    """
    if new_status_name not in EARNING_TRIGGER_STATUSES:
        return None

    already = await earning_repo.earning_exists(referral_id, application_id)
    if already:
        return None

    earning = await earning_repo.create(
        referral_id=referral_id,
        application_id=application_id,
        amount=commission,
    )
    logger.info(
        "Referral earning created | referral=%s application=%s amount=%s",
        referral_id, application_id, commission,
    )
    return earning


async def get_total_earned(account_id: int) -> Decimal:
    return await earning_repo.get_total_earned(account_id)
