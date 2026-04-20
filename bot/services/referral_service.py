from decimal import Decimal
from typing import List, Optional

from bot.models.referral import Referral, ReferralEarning
from bot.repositories.referral_repository import ReferralEarningRepository, ReferralRepository
from bot.utils.logger import get_logger

logger = get_logger(__name__)

referral_repo = ReferralRepository()
earning_repo = ReferralEarningRepository()

# Status names that trigger a referral earning when an application reaches them
EARNING_TRIGGER_STATUSES = {"Bought training"}


async def create_referral_link(account_id: int, name: str, code: str) -> Referral:
    """Create a new referral link. Raises ValueError if code already exists."""
    ...


async def get_referral_by_code(code: str) -> Optional[Referral]:
    ...


async def list_user_referrals(account_id: int) -> List[Referral]:
    ...


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
    ...
