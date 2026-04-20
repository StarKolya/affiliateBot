from aiogram import Bot, F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message

from bot.config import settings
from bot.keyboards.user_kb import main_menu_kb, subscription_check_kb
from bot.services import user_service
from bot.utils.logger import get_logger
from bot.utils.telegram import is_channel_member

logger = get_logger(__name__)
router = Router(name="user")


def _parse_referral_code(args: str | None) -> str | None:
    """Extracts the code from a deep-link payload like 'ref=abc123'."""
    if args and args.startswith("ref="):
        code = args[4:].strip()
        return code or None
    return None


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, bot: Bot) -> None:
    tg_user = message.from_user

    referral_code = _parse_referral_code(command.args)

    account, created = await user_service.get_or_create_user(
        telegram_id=tg_user.id,
        name=tg_user.first_name,
        surname=tg_user.last_name,
        username=tg_user.username,
        referral_code=referral_code,
    )

    if not created:
        # Existing user — subscription already verified at registration, skip check
        logger.info("Returning user | telegram_id=%s", tg_user.id)
        await message.answer(
            f"Welcome back, {account.name}!",
            reply_markup=main_menu_kb(),
        )
        return

    # New user — perform the one-time channel subscription check
    subscribed = await is_channel_member(bot, settings.CHANNEL_ID, tg_user.id)

    if subscribed:
        await user_service.mark_subscription_verified(account)
        await message.answer(
            f"Welcome, {account.name}! You're now registered.",
            reply_markup=main_menu_kb(),
        )
    else:
        await message.answer(
            "To use this bot you must be subscribed to our channel.\n"
            "Please subscribe and then press the button below.",
            reply_markup=subscription_check_kb(settings.CHANNEL_URL),
        )


@router.callback_query(F.data == "check_subscription")
async def callback_check_subscription(callback: CallbackQuery, bot: Bot) -> None:
    tg_user = callback.from_user

    account = await user_service.get_by_telegram_id(tg_user.id)
    if account is None:
        await callback.answer("Please send /start first.", show_alert=True)
        return

    if account.subscription_verified:
        # Edge case: user pressed the button after already being verified
        await callback.message.delete()
        await callback.message.answer(
            "You already have access!",
            reply_markup=main_menu_kb(),
        )
        await callback.answer()
        return

    subscribed = await is_channel_member(bot, settings.CHANNEL_ID, tg_user.id)

    if subscribed:
        await user_service.mark_subscription_verified(account)
        await callback.message.delete()
        await callback.message.answer(
            f"Welcome, {account.name}! You're now registered.",
            reply_markup=main_menu_kb(),
        )
        await callback.answer()
    else:
        await callback.answer(
            "You are not subscribed yet. Please join the channel and try again.",
            show_alert=True,
        )


@router.message()
async def handle_message(message: Message) -> None:
    """Catch-all placeholder for future FSM-driven flows."""
    ...
