from typing import Optional

from bot.models.account import Account
from bot.repositories.referral_repository import ReferralRepository
from bot.repositories.user_repository import RoleRepository, UserRepository
from bot.utils.logger import get_logger

logger = get_logger(__name__)

_user_repo = UserRepository()
_role_repo = RoleRepository()
_referral_repo = ReferralRepository()


async def get_or_create_user(
    telegram_id: int,
    name: str,
    surname: Optional[str],
    username: Optional[str],
    referral_code: Optional[str] = None,
) -> tuple[Account, bool]:
    """
    Returns (account, created).
    - If the user already exists, returns it immediately — no writes.
    - On first registration, resolves the referral code (if any) and creates
      the account in 'Processing' state with subscription_verified=False.
    The subscription check is intentionally NOT done here; the handler decides
    when to trigger it.
    """
    existing = await _user_repo.get_by_telegram_id(telegram_id)
    if existing:
        return existing, False

    default_role = await _role_repo.get_by_name("user")
    if default_role is None:
        raise RuntimeError(
            "Default 'user' role is missing from the database. "
            "Make sure seed_initial_data() ran on startup."
        )

    referred_by = None
    if referral_code:
        referred_by = await _referral_repo.get_by_code(referral_code)
        if referred_by is None:
            logger.warning(
                "Unknown referral code '%s' | telegram_id=%s — registering without referral",
                referral_code,
                telegram_id,
            )

    account = await _user_repo.create_user(
        telegram_id=telegram_id,
        name=name,
        surname=surname,
        username=username,
        role=default_role,
        referred_by=referred_by,
    )

    logger.info(
        "New user registered | telegram_id=%s | referral_code=%s",
        telegram_id,
        referral_code,
    )
    return account, True


async def get_by_telegram_id(telegram_id: int) -> Optional[Account]:
    return await _user_repo.get_by_telegram_id(telegram_id)


async def mark_subscription_verified(account: Account) -> None:
    """Flip subscription_verified=True. Called only once per user lifetime."""
    account.subscription_verified = True
    await account.save(update_fields=["subscription_verified"])
    logger.info("Subscription verified | telegram_id=%s", account.telegram_id)


async def is_subscription_verified(telegram_id: int) -> bool:

    """
    account = await _user_repo.get_by_telegram_id(telegram_id)
    return bool(account and account.subscription_verified)

    """
    return True
    