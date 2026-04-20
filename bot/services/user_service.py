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
    - On first registration, validates the referral code and stores it as a
      plain string on the account (no FK — see Account.referred_by_code).
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

    # Validate the code exists before storing it; silently drop invalid codes
    resolved_code: Optional[str] = None
    if referral_code:
        referral = await _referral_repo.get_by_code(referral_code)
        if referral:
            resolved_code = referral_code
        else:
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
        referred_by_code=resolved_code,
    )

    logger.info(
        "New user registered | telegram_id=%s | referral_code=%s",
        telegram_id,
        resolved_code,
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
    