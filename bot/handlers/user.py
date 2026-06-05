from decimal import Decimal, InvalidOperation

from aiogram import Bot, F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import settings
from bot.exceptions import AlreadyAppliedException
from bot.models.application import JobApplication
from bot.handlers.states import ApplyStates, CreateReferralStates, RequestPayoutStates
from bot.keyboards.user_kb import (
    PAYOUT_HISTORY_PAGE_SIZE,
    REFERRAL_PAGE_SIZE,
    job_detail_kb,
    job_list_kb,
    main_menu_kb,
    niche_list_kb,
    payout_create_kb,
    payout_history_kb,
    payout_menu_kb,
    referral_detail_kb,
    referral_links_list_kb,
    referral_menu_kb,
    referral_stats_kb,
    subscription_check_kb,
)
from bot.services import application_service, job_service, payout_service, referral_service, user_service
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
        except AlreadyAppliedException:
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
        questions=[
            {"id": jq.id, "text": jq.question.description, "type": jq.question.expected_answer_type}
            for jq in questions
        ],
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

    current_q = questions[index]
    if current_q["type"] == "number":
        try:
            float(message.text.replace(",", "."))
        except ValueError:
            await message.answer("Please enter a valid number:")
            return

    answers[str(current_q["id"])] = message.text
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
    except AlreadyAppliedException:
        await message.answer("You have already applied for this job.")
        return

    await message.answer("✅ Your application has been submitted!")


# --- Referral links ---

@router.message(F.text == "🔗 Referral Links")
async def cmd_referral_links(message: Message) -> None:
    await message.answer(
        "👥 <b>Referral Program</b>\n\n"
        "Create referral links, share them, and earn commission every time "
        "someone you referred gets hired.",
        reply_markup=referral_menu_kb(),
    )


@router.callback_query(F.data == "referral_menu")
async def callback_referral_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "👥 <b>Referral Program</b>\n\n"
        "Create referral links, share them, and earn commission every time "
        "someone you referred gets hired.",
        reply_markup=referral_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "referral_stats")
async def callback_referral_stats(callback: CallbackQuery) -> None:
    account = await user_service.get_by_telegram_id(callback.from_user.id)
    stats = await referral_service.get_account_stats(account.id)
    await callback.message.edit_text(
        f"📊 <b>Your Stats</b>\n\n"
        f"👥 Total referred: {stats.total_referred}\n"
        f"📝 Applications: {stats.total_applications}\n"
        f"  ⏳ Pending: {stats.total_pending}\n"
        f"  ❌ Declined: {stats.total_declined}\n"
        f"  🤝 Deal Closed: {stats.total_deal_closed}\n"
        f"  ✅ Joined Team: {stats.total_joined_team}\n"
        f"  📚 Bought Course: {stats.total_bought_course}\n"
        f"💰 Total earned: ${stats.total_earned:.2f}",
        reply_markup=referral_stats_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "referral_links")
async def callback_referral_links(callback: CallbackQuery) -> None:
    await _show_links_page(callback.message, callback.from_user.id, page=0)
    await callback.answer()


@router.callback_query(F.data.startswith("referral_page:"))
async def callback_referral_page(callback: CallbackQuery) -> None:
    page = int(callback.data.split(":")[1])
    await _show_links_page(callback.message, callback.from_user.id, page=page)
    await callback.answer()


async def _show_links_page(target: Message, telegram_id: int, page: int) -> None:
    account = await user_service.get_by_telegram_id(telegram_id)
    links = await referral_service.list_user_referrals(account.id)
    total_pages = max(1, -(-len(links) // REFERRAL_PAGE_SIZE))
    page = min(page, total_pages - 1)
    page_links = links[page * REFERRAL_PAGE_SIZE:(page + 1) * REFERRAL_PAGE_SIZE]

    counts: dict = {}
    if page_links:
        rows = await JobApplication.filter(
            referral_id__in=[l.id for l in page_links]
        ).values("referral_id")
        for row in rows:
            rid = row["referral_id"]
            counts[rid] = counts.get(rid, 0) + 1

    if links:
        text = f"🔗 <b>Your Links</b>  (page {page + 1}/{total_pages})"
    else:
        text = "🔗 <b>Your Links</b>\n\nYou have no referral links yet. Create one to start earning!"

    await target.edit_text(text, reply_markup=referral_links_list_kb(page_links, page, total_pages, counts))


@router.callback_query(F.data.startswith("referral_detail:"))
async def callback_referral_detail(callback: CallbackQuery) -> None:
    referral_id = int(callback.data.split(":")[1])
    account = await user_service.get_by_telegram_id(callback.from_user.id)
    links = await referral_service.list_user_referrals(account.id)
    referral = next((r for r in links if r.id == referral_id), None)
    if referral is None:
        await callback.answer("Link not found.", show_alert=True)
        return
    stats = await referral_service.get_referral_stats(referral)
    link = f"https://t.me/{settings.BOT_USERNAME}?start=ref={referral.code}"
    await callback.message.edit_text(
        f"🔗 <b>{referral.name}</b>\n\n"
        f"👥 Referred: {stats.referred_users}\n"
        f"📝 Applications: {stats.applications}\n"
        f"  ⏳ Pending: {stats.pending}\n"
        f"  ❌ Declined: {stats.declined}\n"
        f"  🤝 Deal Closed: {stats.deal_closed}\n"
        f"  ✅ Joined Team: {stats.joined_team}\n"
        f"  📚 Bought Course: {stats.bought_course}\n"
        f"💰 Earned: ${stats.earned:.2f}\n\n"
        f"<code>{link}</code>",
        reply_markup=referral_detail_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "referral_create")
async def callback_referral_create(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CreateReferralStates.enter_name)
    await callback.message.edit_text(
        "Enter a name for this referral link (e.g. <i>Instagram</i>, <i>Friends</i>):"
    )
    await callback.answer()


@router.message(CreateReferralStates.enter_name)
async def fsm_referral_enter_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if len(name) > 50:
        await message.answer("Name is too long. Please keep it under 50 characters:")
        return

    account = await user_service.get_by_telegram_id(message.from_user.id)
    await state.clear()

    referral = await referral_service.create_referral_link(account_id=account.id, name=name)
    link = f"https://t.me/{settings.BOT_USERNAME}?start=ref={referral.code}"
    await message.answer(
        f"✅ <b>{referral.name}</b> created!\n\n"
        f"<code>{link}</code>\n\n"
        "Share this link — you'll earn commission when your referrals get hired.",
        reply_markup=referral_menu_kb(),
    )


# --- Payouts ---

async def _show_payout_menu(target: Message, telegram_id: int, edit: bool = True) -> None:
    account = await user_service.get_by_telegram_id(telegram_id)
    summary = await payout_service.get_user_summary(account.id)
    text = (
        f"💰 <b>Payouts</b>\n\n"
        f"⏳ Pending: ${summary.pending_amount:.2f}\n"
        f"✅ Paid out: ${summary.paid_out_amount:.2f}\n"
        f"💵 Available: ${summary.available_amount:.2f}"
    )
    kb = payout_menu_kb(has_available=summary.available_amount > 0)
    if edit:
        await target.edit_text(text, reply_markup=kb)
    else:
        await target.answer(text, reply_markup=kb)


@router.message(F.text == "💰 Request Payout")
async def cmd_payout_menu(message: Message) -> None:
    await _show_payout_menu(message, message.from_user.id, edit=False)


@router.callback_query(F.data == "payout_menu")
async def callback_payout_menu(callback: CallbackQuery) -> None:
    await _show_payout_menu(callback.message, callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data == "payout_history")
async def callback_payout_history(callback: CallbackQuery) -> None:
    await _show_payout_history_page(callback.message, callback.from_user.id, page=0)
    await callback.answer()


@router.callback_query(F.data.startswith("payout_history_page:"))
async def callback_payout_history_page(callback: CallbackQuery) -> None:
    page = int(callback.data.split(":")[1])
    await _show_payout_history_page(callback.message, callback.from_user.id, page=page)
    await callback.answer()


async def _show_payout_history_page(target: Message, telegram_id: int, page: int) -> None:
    account = await user_service.get_by_telegram_id(telegram_id)
    payouts = await payout_service.list_user_payouts(account.id)
    total_pages = max(1, -(-len(payouts) // PAYOUT_HISTORY_PAGE_SIZE))
    page = min(page, total_pages - 1)
    page_payouts = payouts[page * PAYOUT_HISTORY_PAGE_SIZE:(page + 1) * PAYOUT_HISTORY_PAGE_SIZE]

    STATUS_ICON = {"pending": "⏳", "approved": "✅", "rejected": "❌"}
    if page_payouts:
        lines = [f"📋 <b>Payout History</b>  (page {page + 1}/{total_pages})\n"]
        for p in page_payouts:
            icon = STATUS_ICON.get(p.status, "•")
            date = p.created_at.strftime("%d %b %Y")
            lines.append(f"{icon} ${p.amount:.2f} — {p.status} — {date}")
        text = "\n".join(lines)
    else:
        text = "📋 <b>Payout History</b>\n\nNo payout requests yet."

    await target.edit_text(text, reply_markup=payout_history_kb(page_payouts, page, total_pages))


@router.callback_query(F.data == "payout_create")
async def callback_payout_create(callback: CallbackQuery, state: FSMContext) -> None:
    account = await user_service.get_by_telegram_id(callback.from_user.id)
    summary = await payout_service.get_user_summary(account.id)
    await state.set_state(RequestPayoutStates.enter_amount)
    await state.update_data(account_id=account.id, available=str(summary.available_amount))
    await callback.message.edit_text(
        f"Enter the amount to request, or tap the button below to request everything available:",
        reply_markup=payout_create_kb(summary.available_amount),
    )
    await callback.answer()


@router.callback_query(RequestPayoutStates.enter_amount, F.data == "payout_all_available")
async def callback_payout_all_available(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()
    amount = Decimal(data["available"])
    account_id = data["account_id"]
    try:
        await payout_service.request_payout(account_id=account_id, amount=amount)
    except ValueError as e:
        await callback.answer(str(e), show_alert=True)
        return
    await callback.message.edit_text(
        f"✅ Payout request for <b>${amount:.2f}</b> submitted!",
        reply_markup=payout_menu_kb(has_available=False),
    )
    await callback.answer()


@router.message(RequestPayoutStates.enter_amount)
async def fsm_payout_enter_amount(message: Message, state: FSMContext) -> None:
    try:
        amount = Decimal(message.text.strip().replace(",", "."))
    except InvalidOperation:
        await message.answer("Please enter a valid number:")
        return
    if amount <= 0:
        await message.answer("Amount must be greater than zero:")
        return

    data = await state.get_data()
    available = Decimal(data["available"])
    if amount > available:
        await message.answer(f"Amount exceeds your available balance (${available:.2f}). Enter a lower amount:")
        return

    await state.clear()
    try:
        await payout_service.request_payout(account_id=data["account_id"], amount=amount)
    except ValueError as e:
        await message.answer(str(e))
        return
    await message.answer(
        f"✅ Payout request for <b>${amount:.2f}</b> submitted!",
        reply_markup=payout_menu_kb(has_available=False),
    )
