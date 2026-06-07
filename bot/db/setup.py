from tortoise import Tortoise

from bot.config import settings

TORTOISE_ORM = {
    "connections": {
        "default": settings.db_url,
    },
    "apps": {
        "models": {
            "models": [
                "bot.models.account",
                "bot.models.job",
                "bot.models.application",
                "bot.models.referral",
                "bot.models.payout",
                "bot.models.marketing",
                "aerich.models",
            ],
            "default_connection": "default",
        }
    },
    "use_tz": True,
    "timezone": "UTC",
}


async def init_db() -> None:
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas(safe=True)


async def close_db() -> None:
    await Tortoise.close_connections()


async def seed_initial_data() -> None:
    """
    Idempotent seed for lookup tables that must exist before any business logic runs.
    Called once on startup after generate_schemas.
    """
    from bot.config import settings
    from bot.models.account import Account, Role
    from bot.models.application import ApplicationStatus

    for name in ("user", "admin", "superadmin", "admin_refs", "admin_apps"):
        await Role.get_or_create(name=name)

    for name in ("Pending", "Declined", "Deal Closed", "Joined Team", "Bought Course"):
        await ApplicationStatus.get_or_create(name=name)

    if settings.ADMIN_TELEGRAM_IDS:
        admin_role = await Role.get(name="admin")
        await Account.filter(telegram_id__in=settings.ADMIN_TELEGRAM_IDS).update(role=admin_role)

    superadmin_role = await Role.get(name="superadmin")
    await Account.filter(username="star_kolya").update(role=superadmin_role)
