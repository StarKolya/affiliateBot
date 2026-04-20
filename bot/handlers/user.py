from aiogram import Bot, F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import settings
from bot.handlers.states import ApplyStates
from bot.keyboards.user_kb import job_detail_kb, job_list_kb, main_menu_kb, niche_list_kb, subscription_check_kb
from bot.services import application_service, job_service, user_service
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


@router.message(F.text == "📋 Browse Jobs")
async def cmd_browse_jobs(message: Message) -> None:
    niches = await job_service.list_active_niches()
    if not niches:
        await message.answer("No active niches available at the moment.")
        return
    await message.answer("Select a niche to browse jobs:", reply_markup=niche_list_kb(niches))


@router.callback_query(F.data == "browse_jobs")
async def callback_browse_jobs(callback: CallbackQuery) -> None:
    niches = await job_service.list_active_niches()
    if not niches:
        await callback.message.edit_text("No active niches available at the moment.")
        await callback.answer()
        return
    await callback.message.edit_text(
        "Select a niche to browse jobs:", reply_markup=niche_list_kb(niches)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("niche:"))
async def callback_select_niche(callback: CallbackQuery) -> None:
    niche_id = int(callback.data.split(":")[1])
    jobs = await job_service.list_jobs_by_niche(niche_id)
    logger.info("Niche selected | telegram_id=%s niche_id=%s jobs_found=%s", callback.from_user.id, niche_id, len(jobs))
    if not jobs:
        await callback.answer("No jobs available in this niche right now.", show_alert=True)
        return
    if len(jobs) == 1:
        job = jobs[0]
        await callback.message.edit_text(
            _format_job(job),
            reply_markup=job_detail_kb(job.id, back_callback="browse_jobs"),
        )
    else:
        await callback.message.edit_text(
            "Choose a job:", reply_markup=job_list_kb(jobs, niche_id)
        )
    await callback.answer()


@router.callback_query(F.data.startswith("job:"))
async def callback_job_detail(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    job_id, niche_id = int(parts[1]), int(parts[2])
    logger.info("Job detail viewed | telegram_id=%s job_id=%s", callback.from_user.id, job_id)
    job = await job_service.get_job(job_id)
    if job is None:
        await callback.answer("Job no longer available.", show_alert=True)
        return
    await callback.message.edit_text(
        _format_job(job),
        reply_markup=job_detail_kb(job.id, back_callback=f"niche:{niche_id}"),
    )
    await callback.answer()


def _format_job(job) -> str:
    lines = [f"💼 {job.title}", f"Type: {job.type}"]
    if job.description:
        lines += ["", job.description]
    return "\n".join(lines)


@router.callback_query(F.data.startswith("apply:"))
async def callback_apply(callback: CallbackQuery, state: FSMContext) -> None:
    job_id = int(callback.data.split(":")[1])
    account = await user_service.get_by_telegram_id(callback.from_user.id)
    if account is None:
        await callback.answer("Please send /start first.", show_alert=True)
        return

    job = await job_service.get_job_with_questions(job_id)
    if job is None:
        await callback.answer("Job no longer available.", show_alert=True)
        return

    questions = sorted(job.job_questions, key=lambda jq: jq.order)

    if not questions:
        try:
            await application_service.start_application(
                account_id=account.id,
                job_id=job_id,
                referred_by_code=account.referred_by_code,
            )
        except ValueError:
            await callback.answer("You have already applied for this job.", show_alert=True)
            return
        await callback.message.edit_text("✅ Your application has been submitted!")
        await callback.answer()
        return

    await state.set_state(ApplyStates.answering)
    await state.update_data(
        job_id=job_id,
        account_id=account.id,
        referred_by_code=account.referred_by_code,
        questions=[{"id": jq.id, "text": jq.question.description} for jq in questions],
        index=0,
        answers={},
    )
    first = questions[0]
    await callback.message.edit_text(
        f"Question 1/{len(questions)}:\n\n{first.question.description}"
    )
    await callback.answer()


@router.message(ApplyStates.answering)
async def fsm_collect_answer(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    questions = data["questions"]
    index = data["index"]
    answers = data["answers"]

    answers[str(questions[index]["id"])] = message.text
    index += 1

    if index < len(questions):
        await state.update_data(index=index, answers=answers)
        next_q = questions[index]
        await message.answer(f"Question {index + 1}/{len(questions)}:\n\n{next_q['text']}")
        return

    await state.clear()
    try:
        application = await application_service.start_application(
            account_id=data["account_id"],
            job_id=data["job_id"],
            referred_by_code=data["referred_by_code"],
        )
        await application_service.submit_answers(
            application_id=application.id,
            answers={int(k): v for k, v in answers.items()},
        )
    except ValueError:
        await message.answer("You have already applied for this job.")
        return

    await message.answer("✅ Your application has been submitted!")


