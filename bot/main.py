import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.db import close_db, init_db, seed_initial_data, seed_test_data
from bot.handlers import build_main_router
from bot.middlewares import ErrorHandlerMiddleware
from bot.scheduler import build_scheduler
from bot.utils import setup_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    setup_logging(level=logging.INFO)
    logger.info("Starting affiliate bot")

    await init_db()
    await seed_initial_data()
    await seed_test_data()  # TODO: remove before production
    logger.info("Database connected and seeded")

    scheduler = build_scheduler()
    scheduler.start()
    logger.info("Scheduler started")

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Global error handler wraps all updates
    dp.update.outer_middleware(ErrorHandlerMiddleware())

    dp.include_router(build_main_router())

    logger.info("Bot polling started")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown(wait=False)
        await close_db()
        await bot.session.close()
        logger.info("Bot shut down cleanly")


if __name__ == "__main__":
    asyncio.run(main())
