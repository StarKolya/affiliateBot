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
    from bot.models.account import Role
    from bot.models.application import ApplicationStatus

    for name in ("user", "admin"):
        await Role.get_or_create(name=name)

    for name in ("Processing", "Not accepted", "Bought training", "Joined team"):
        await ApplicationStatus.get_or_create(name=name)
