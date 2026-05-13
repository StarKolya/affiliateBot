from decimal import Decimal, InvalidOperation
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto, Message

from bot.config import settings
from bot.models.application import JobApplication
from bot.handlers.states import ApplyStates, CreateReferralStates, RequestPayoutStates
from bot.keyboards.user_kb import (
    PAYOUT_HISTORY_PAGE_SIZE,
    REFERRAL_PAGE_SIZE,
    apply_cancel_kb,
    apply_yesno_kb,
    job_detail_kb,
    job_list_kb,
    main_menu_kb,
    niche_list_kb,
    payout_create_kb,
    payout_wallet_cancel_kb,
    payout_history_kb,
    payout_menu_kb,
    referral_create_type_kb,
    referral_detail_kb,
    referral_job_select_kb,
    referral_links_list_kb,
    referral_menu_kb,
    referral_stats_kb,
    subscription_check_kb,
)
from bot.services import application_service, job_service, payout_service, referral_service, user_service
from bot.utils.logger import get_logger
from bot.utils.telegram import is_subscribed_to_all

logger = get_logger(__name__)
router = Router(name="user")

_START_IMAGE = Path(__file__).parent.parent / "images" / "start.jpg"
_SUBSCRIBED_IMAGE = Path(__file__).parent.parent / "images" / "subscribed.jpg"
_NICHE_IMAGE = Path(__file__).parent.parent / "images" / "niche.jpg"
_OFFER_IMAGE = Path(__file__).parent.parent / "images" / "offer.jpg"
_REFERRAL_IMAGE = Path(__file__).parent.parent / "images" / "referral.jpg"
_STATS_IMAGE = Path(__file__).parent.parent / "images" / "statistics.jpg"
_FINANCE_IMAGE = Path(__file__).parent.parent / "images" / "finance.jpg"
_TRANSACTION_IMAGE = Path(__file__).parent.parent / "images" / "transaction_history.jpg"
_MY_LINKS_IMAGE = Path(__file__).parent.parent / "images" / "my_links.jpg"


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

    channel_ids = [settings.CHANNEL_ID] + ([settings.CHANNEL_ID_2] if settings.CHANNEL_ID_2 else [])
    subscribed = await is_subscribed_to_all(bot, channel_ids, tg_user.id)

    if not subscribed:
        await message.answer_photo(
            FSInputFile(_SUBSCRIBED_IMAGE),
            caption=f"🫵 Приветствую, {tg_user.first_name}!\n"
            "Пожалуйста, подпишитесь на канал(ы), чтобы использовать Jobs Network!",
            reply_markup=subscription_check_kb(settings.CHANNEL_URL, settings.CHANNEL_URL_2),
        )
        return

    if created:
        await user_service.mark_subscription_verified(account)

    bound_job = None
    if referral_code:
        referral = await referral_service.get_referral_by_code(referral_code)
        if referral and referral.job_posting_id:
            bound_job = await job_service.get_job(referral.job_posting_id)

    if bound_job:
        await message.answer_photo(
            FSInputFile(_START_IMAGE),
            caption=f"<b>Добро пожаловать, {account.name}!</b>",
            reply_markup=main_menu_kb(),
        )
        await message.answer(
            _format_job(bound_job),
            reply_markup=job_detail_kb(bound_job.id, back_callback="browse_jobs"),
        )
    else:
        await message.answer_photo(
            FSInputFile(_START_IMAGE),
            caption=f"<b>Добро пожаловать, {account.name}!\n\n"
            "🌐 Ты попал в Jobs Network\n"
            "<blockquote>место, где находят себя в digital-индустрии</blockquote>\n\n"
            "🫵 Здесь тебя ждут:\n"
            "<blockquote>🔹 Удалённые вакансии\n"
            "🔹 Арбитраж трафика\n"
            "🔹 Работа с инфлюенсерами</blockquote>\n\n"
            "Найди себя прямо сейчас 👇</b>",
            reply_markup=main_menu_kb(),
        )


@router.callback_query(F.data == "check_subscription")
async def callback_check_subscription(callback: CallbackQuery, bot: Bot) -> None:
    tg_user = callback.from_user

    account = await user_service.get_by_telegram_id(tg_user.id)
    if account is None:
        await callback.answer("Сначала отправь /start.", show_alert=True)
        return

    channel_ids = [settings.CHANNEL_ID] + ([settings.CHANNEL_ID_2] if settings.CHANNEL_ID_2 else [])
    subscribed = await is_subscribed_to_all(bot, channel_ids, tg_user.id)

    await callback.answer()

    if subscribed:
        if not account.subscription_verified:
            await user_service.mark_subscription_verified(account)
        await callback.message.delete()

        bound_job = None
        if account.referred_by_code:
            referral = await referral_service.get_referral_by_code(account.referred_by_code)
            if referral and referral.job_posting_id:
                bound_job = await job_service.get_job(referral.job_posting_id)

        await callback.message.answer_photo(
            FSInputFile(_START_IMAGE),
            caption=f"<b>Добро пожаловать, {account.name}!</b>" if bound_job else
            f"<b>Добро пожаловать, {account.name}!\n\n"
            "🌐 Ты попал в Jobs Network\n"
            "<blockquote>место, где находят себя в digital-индустрии</blockquote>\n\n"
            "🫵 Здесь тебя ждут:\n"
            "<blockquote>🔹 Удалённые вакансии\n"
            "🔹 Арбитраж трафика\n"
            "🔹 Работа с инфлюенсерами</blockquote>\n\n"
            "Найди себя прямо сейчас 👇</b>",
            reply_markup=main_menu_kb(),
        )

        if bound_job:
            await callback.message.answer(
                _format_job(bound_job),
                reply_markup=job_detail_kb(bound_job.id, back_callback="browse_jobs"),
            )
    else:
        try:
            await callback.message.edit_caption(
                caption=f"❌ Вы ещё не подписались!\n\n"
                f"🫵 Приветствую, {account.name}!\n"
                "Пожалуйста, подпишитесь на канал(ы), чтобы использовать Jobs Network!",
                reply_markup=subscription_check_kb(settings.CHANNEL_URL, settings.CHANNEL_URL_2),
            )
        except TelegramBadRequest:
            pass  # message already shows this text — nothing to update


@router.message(F.text == "📋 Вакансии")
async def cmd_browse_jobs(message: Message) -> None:
    niches = await job_service.list_active_niches()
    if not niches:
        await message.answer("<b>Нет доступных направлений.</b>")
        return
    await message.answer_photo(
        FSInputFile(_NICHE_IMAGE),
        caption="<b><blockquote>📁 Выберите направление:</blockquote></b>",
        reply_markup=niche_list_kb(niches),
    )


@router.callback_query(F.data == "browse_jobs")
async def callback_browse_jobs(callback: CallbackQuery) -> None:
    niches = await job_service.list_active_niches()
    if not niches:
        await callback.message.edit_caption(caption="<b>Нет доступных направлений.</b>")
        await callback.answer()
        return
    await callback.message.edit_media(
        InputMediaPhoto(
            media=FSInputFile(_NICHE_IMAGE),
            caption="<b><blockquote>📁 Выберите направление:</blockquote></b>",
        ),
        reply_markup=niche_list_kb(niches),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("niche:"))
async def callback_select_niche(callback: CallbackQuery) -> None:
    niche_id = int(callback.data.split(":")[1])
    jobs = await job_service.list_jobs_by_niche(niche_id)
    logger.info("Niche selected | telegram_id=%s niche_id=%s jobs_found=%s", callback.from_user.id, niche_id, len(jobs))
    if not jobs:
        await callback.answer("В этом направлении пока нет вакансий.", show_alert=True)
        return
    if len(jobs) == 1:
        job = jobs[0]
        await callback.message.delete()
        await callback.message.answer(
            _format_job(job),
            reply_markup=job_detail_kb(job.id, back_callback="browse_jobs"),
        )
    else:
        await callback.message.edit_media(
            InputMediaPhoto(
                media=FSInputFile(_OFFER_IMAGE),
                caption="<b><blockquote>📋 Выберите вакансию:</blockquote></b>",
            ),
            reply_markup=job_list_kb(jobs, niche_id),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("job:"))
async def callback_job_detail(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    job_id, niche_id = int(parts[1]), int(parts[2])
    logger.info("Job detail viewed | telegram_id=%s job_id=%s", callback.from_user.id, job_id)
    job = await job_service.get_job(job_id)
    if job is None:
        await callback.answer("Вакансия больше недоступна.", show_alert=True)
        return
    await callback.message.delete()
    await callback.message.answer(
        _format_job(job),
        reply_markup=job_detail_kb(job.id, back_callback=f"niche:{niche_id}"),
    )
    await callback.answer()


def _format_job(job) -> str:
    lines = [f"<b><blockquote>💻 Название вакансии</blockquote></b>", job.title]
    if job.description:
        lines += ["", f"<b><blockquote>📑 Описание:</blockquote></b>", job.description]
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
        await callback.answer("Вакансия больше недоступна.", show_alert=True)
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
            await callback.answer("Вы уже откликались на эту вакансию.", show_alert=True)
            return
        await callback.message.edit_text("✅ Ваша заявка отправлена!")
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
    first_q = {"id": questions[0].id, "text": questions[0].question.description, "type": questions[0].question.expected_answer_type}
    await callback.message.edit_text(
        f"<b>Вопрос 1/{len(questions)}:</b>\n\n{first_q['text']}",
        reply_markup=_question_kb(first_q),
    )
    await callback.answer()


def _question_kb(q: dict):
    return apply_yesno_kb() if q["type"] == "yes_no" else apply_cancel_kb()


async def _finish_application(target: Message, data: dict) -> None:
    try:
        application = await application_service.start_application(
            account_id=data["account_id"],
            job_id=data["job_id"],
            referred_by_code=data["referred_by_code"],
        )
        await application_service.submit_answers(
            application_id=application.id,
            answers={int(k): v for k, v in data["answers"].items()},
        )
    except ValueError:
        await target.answer("Вы уже откликались на эту вакансию.")
        return
    await target.answer("<b>🟢 Ваша заявка принята! Менеджер свяжеться с вами 🫵</b>", parse_mode="HTML")


@router.message(ApplyStates.answering)
async def fsm_collect_answer(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    questions = data["questions"]
    index = data["index"]
    answers = data["answers"]

    current_q = questions[index]
    if current_q["type"] == "yes_no":
        await message.answer("Пожалуйста, используйте кнопки Да / Нет:")
        return
    if current_q["type"] == "number":
        try:
            float(message.text.replace(",", "."))
        except ValueError:
            await message.answer("Пожалуйста, введите корректное число:")
            return

    answers[str(current_q["id"])] = message.text
    index += 1

    if index < len(questions):
        await state.update_data(index=index, answers=answers)
        next_q = questions[index]
        await message.answer(
            f"<b>Вопрос {index + 1}/{len(questions)}:</b>\n\n{next_q['text']}",
            reply_markup=_question_kb(next_q),
        )
        return

    await state.clear()
    await _finish_application(message, {**data, "answers": answers})


@router.callback_query(ApplyStates.answering, F.data.startswith("apply_yesno:"))
async def callback_apply_yesno(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    questions = data["questions"]
    index = data["index"]
    answers = data["answers"]

    answer = "Да" if callback.data.split(":")[1] == "yes" else "Нет"
    answers[str(questions[index]["id"])] = answer
    index += 1

    if index < len(questions):
        await state.update_data(index=index, answers=answers)
        next_q = questions[index]
        await callback.message.edit_text(
            f"<b>Вопрос {index + 1}/{len(questions)}:</b>\n\n{next_q['text']}",
            reply_markup=_question_kb(next_q),
        )
        await callback.answer()
        return

    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await _finish_application(callback.message, {**data, "answers": answers})
    await callback.answer()


@router.callback_query(ApplyStates.answering, F.data == "apply_cancel")
async def callback_apply_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Заявка отменена.")
    await callback.answer()


# --- Referral links ---

_REFERRAL_CAPTION = (
    "<b><blockquote>👥 Jobs Network Partners</blockquote>\n\n"
    "📊 Лей трафик — забирай максимум с каждого лида.\n\n"
    "<blockquote>🔴 Без ограничений</blockquote>\n"
    "<blockquote>🔵 Только результат</blockquote></b>"
)


@router.message(F.text == "👥 JN Partners")
async def cmd_referral_links(message: Message) -> None:
    await message.answer_photo(
        FSInputFile(_REFERRAL_IMAGE),
        caption=_REFERRAL_CAPTION,
        reply_markup=referral_menu_kb(),
    )


@router.callback_query(F.data == "referral_menu")
async def callback_referral_menu(callback: CallbackQuery) -> None:
    await callback.message.delete()
    await callback.message.answer_photo(
        FSInputFile(_REFERRAL_IMAGE),
        caption=_REFERRAL_CAPTION,
        reply_markup=referral_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "referral_stats")
async def callback_referral_stats(callback: CallbackQuery) -> None:
    account = await user_service.get_by_telegram_id(callback.from_user.id)
    stats = await referral_service.get_account_stats(account.id)
    await callback.message.edit_media(
        InputMediaPhoto(
            media=FSInputFile(_STATS_IMAGE),
            caption=(
                f"<b><blockquote>📊 Статистика</blockquote>\n\n"
                f"👥 Активации: {stats.total_referred}\n"
                f"📝 Отклики: {stats.total_applications}\n"
                f"⌛️ В обработке: {stats.total_pending}\n"
                f"🪫 Отклонено: {stats.total_declined}\n"
                f"✅ Принято: {stats.total_joined_team}\n"
                f"📚 Обучение: {stats.total_bought_course}\n\n"
                f"💰 Доход: ${stats.total_earned:.2f}</b>"

            ),
        ),
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

    page_indicator = f"  стр. {page + 1}/{total_pages}"
    caption = f"<b><blockquote>🔗 Мои ссылки ({len(links)})</blockquote></b>\n{page_indicator}"
    kb = referral_links_list_kb(page_links, page, total_pages, counts)

    if target.photo:
        await target.edit_media(
            InputMediaPhoto(media=FSInputFile(_MY_LINKS_IMAGE), caption=caption),
            reply_markup=kb,
        )
    else:
        await target.delete()
        await target.answer_photo(FSInputFile(_MY_LINKS_IMAGE), caption=caption, reply_markup=kb)


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
    await callback.message.delete()
    await callback.message.answer(
        f"<b><blockquote>🔗 {referral.name}</blockquote>\n\n"
        f"👥 Активации: {stats.referred_users}\n"
        f"📝 Отклики: {stats.applications}\n"
        f"⌛️ В обработке: {stats.pending}\n"
        f"🪫 Отклонено: {stats.declined}\n"
        f"✅ Принято: {stats.joined_team}\n"
        f"📚 Обучение: {stats.bought_course}\n\n"
        f"💰 Доход: ${stats.earned:.2f}</b>\n\n"
        f"<code>{link}</code>",
        reply_markup=referral_detail_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "referral_create")
async def callback_referral_create(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CreateReferralStates.enter_name)
    await callback.message.delete()
    await callback.message.answer(
        "Введи название для реферальной ссылки (например: <i>Instagram</i>, <i>Друзья</i>):"
    )
    await callback.answer()


@router.message(CreateReferralStates.enter_name)
async def fsm_referral_enter_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if len(name) > 50:
        await message.answer("Слишком длинное название. Максимум 50 символов:")
        return

    await state.update_data(referral_name=name)
    await state.set_state(CreateReferralStates.select_type)
    await message.answer(
        "Выбери тип ссылки:\n\n"
        "<b>🔗 Обычная</b> — пользователь попадает на главное меню бота\n"
        "<b>💼 Привязать к вакансии</b> — пользователь сразу открывает конкретную вакансию",
        reply_markup=referral_create_type_kb(),
    )


@router.callback_query(CreateReferralStates.select_type, F.data == "referral_type:free")
async def callback_referral_type_free(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()
    account = await user_service.get_by_telegram_id(callback.from_user.id)
    referral = await referral_service.create_referral_link(account_id=account.id, name=data["referral_name"])
    link = f"https://t.me/{settings.BOT_USERNAME}?start=ref={referral.code}"
    await callback.message.edit_text(
        f"✅ <b>{referral.name}</b> создана!\n\n"
        f"<code>{link}</code>\n\n"
        "Делись ссылкой — получай комиссию с каждого нанятого реферала.",
        reply_markup=referral_menu_kb(),
    )
    await callback.answer()


@router.callback_query(CreateReferralStates.select_type, F.data == "referral_type:job")
async def callback_referral_type_job(callback: CallbackQuery, state: FSMContext) -> None:
    jobs = await job_service.list_active_jobs()
    if not jobs:
        await callback.answer("Нет доступных вакансий.", show_alert=True)
        return
    await state.set_state(CreateReferralStates.select_job)
    await callback.message.edit_text(
        "Выбери вакансию, к которой привязать ссылку:",
        reply_markup=referral_job_select_kb(jobs),
    )
    await callback.answer()


@router.callback_query(CreateReferralStates.select_job, F.data.startswith("referral_bind_job:"))
async def callback_referral_bind_job(callback: CallbackQuery, state: FSMContext) -> None:
    job_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    await state.clear()
    account = await user_service.get_by_telegram_id(callback.from_user.id)
    job = await job_service.get_job(job_id)
    if job is None:
        await callback.answer("Вакансия больше недоступна.", show_alert=True)
        return
    referral = await referral_service.create_referral_link(
        account_id=account.id,
        name=data["referral_name"],
        job_posting_id=job_id,
    )
    link = f"https://t.me/{settings.BOT_USERNAME}?start=ref={referral.code}"
    await callback.message.edit_text(
        f"✅ <b>{referral.name}</b> создана!\n"
        f"📌 Привязана к: <b>{job.title}</b>\n\n"
        f"<code>{link}</code>\n\n"
        "Пользователь сразу попадёт на эту вакансию.",
        reply_markup=referral_menu_kb(),
    )
    await callback.answer()


# --- Payouts ---

async def _show_payout_menu(target: Message, telegram_id: int, edit: bool = True) -> None:
    account = await user_service.get_by_telegram_id(telegram_id)
    summary = await payout_service.get_user_summary(account.id)
    caption = (
        f"<b><blockquote>💰 Финансы</blockquote>\n\n"
        f"💵 Баланс: ${summary.available_amount:.2f}\n"
        f"⌛️ В обработке: ${summary.pending_amount:.2f}\n"
        f"✅ Выплачено: ${summary.paid_out_amount:.2f}\n\n"
        f"<blockquote>👉 Средства на балансе доступны для вывода</blockquote></b>"
    )
    kb = payout_menu_kb(has_available=summary.available_amount > 0)
    if edit:
        await target.edit_media(
            InputMediaPhoto(media=FSInputFile(_FINANCE_IMAGE), caption=caption),
            reply_markup=kb,
        )
    else:
        await target.answer_photo(FSInputFile(_FINANCE_IMAGE), caption=caption, reply_markup=kb)


@router.message(F.text == "💼 Финансы")
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
    STATUS_RU = {"pending": "В обработке", "approved": "Выплачено", "rejected": "Отклонено"}
    if page_payouts:
        lines = [f"<b><blockquote>📋 История выплат</blockquote>\n"]
        for p in page_payouts:
            icon = STATUS_ICON.get(p.status, "•")
            status = STATUS_RU.get(p.status, p.status)
            date = p.created_at.strftime("%d %b %Y")
            lines.append(f"{icon} ${p.amount:.2f} — {status} — {date}")
        caption = "\n".join(lines) + "</b>"
    else:
        caption = (
            "<b><blockquote>📋 История выплат</blockquote>\n\n"
            "🪫 Пока нет транзакций\n"
            "<blockquote>Начни привлекать трафик, чтобы получить первую выплату 🫵</blockquote></b>"
        )

    await target.edit_media(
        InputMediaPhoto(media=FSInputFile(_TRANSACTION_IMAGE), caption=caption),
        reply_markup=payout_history_kb(page_payouts, page, total_pages),
    )


@router.callback_query(F.data == "payout_create")
async def callback_payout_create(callback: CallbackQuery, state: FSMContext) -> None:
    account = await user_service.get_by_telegram_id(callback.from_user.id)
    summary = await payout_service.get_user_summary(account.id)
    await state.set_state(RequestPayoutStates.enter_amount)
    await state.update_data(account_id=account.id, available=str(summary.available_amount))
    await callback.message.edit_media(
        InputMediaPhoto(
            media=FSInputFile(_FINANCE_IMAGE),
            caption="<b><blockquote>💰 Финансы</blockquote>\n\nВведи сумму или нажми кнопку ниже, чтобы вывести всё доступное:</b>",
        ),
        reply_markup=payout_create_kb(summary.available_amount),
    )
    await callback.answer()


_WALLET_PROMPT = (
    "<b><blockquote>💰 Финансы</blockquote>\n\n"
    "Введи адрес кошелька <b>USDT TRC20</b>:\n\n"
    "<blockquote>⚠️ Убедись, что адрес именно в сети TRC20.\n"
    "Средства, отправленные на адрес другой сети, будут безвозвратно потеряны.</blockquote></b>"
)


@router.callback_query(RequestPayoutStates.enter_amount, F.data == "payout_all_available")
async def callback_payout_all_available(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    amount = Decimal(data["available"])
    await state.update_data(payout_amount=str(amount))
    await state.set_state(RequestPayoutStates.enter_wallet)
    await callback.message.edit_media(
        InputMediaPhoto(media=FSInputFile(_FINANCE_IMAGE), caption=_WALLET_PROMPT),
        reply_markup=payout_wallet_cancel_kb(),
    )
    await callback.answer()


@router.message(RequestPayoutStates.enter_amount)
async def fsm_payout_enter_amount(message: Message, state: FSMContext) -> None:
    try:
        amount = Decimal(message.text.strip().replace(",", "."))
    except InvalidOperation:
        await message.answer("Пожалуйста, введите корректное число:")
        return
    if amount <= 0:
        await message.answer("Сумма должна быть больше нуля:")
        return

    data = await state.get_data()
    available = Decimal(data["available"])
    if amount > available:
        await message.answer(f"Сумма превышает доступный баланс (${available:.2f}). Введи меньшую сумму:")
        return

    await state.update_data(payout_amount=str(amount))
    await state.set_state(RequestPayoutStates.enter_wallet)
    await message.answer_photo(
        FSInputFile(_FINANCE_IMAGE),
        caption=_WALLET_PROMPT,
        reply_markup=payout_wallet_cancel_kb(),
    )


@router.message(RequestPayoutStates.enter_wallet)
async def fsm_payout_enter_wallet(message: Message, state: FSMContext) -> None:
    wallet = message.text.strip()
    if not (wallet.startswith("T") and len(wallet) == 34 and wallet.isalnum()):
        await message.answer(
            "❌ Неверный формат адреса. Адрес USDT TRC20 начинается с <b>T</b> и содержит <b>34 символа</b>.\n\nПопробуй ещё раз:",
            reply_markup=payout_wallet_cancel_kb(),
        )
        return

    data = await state.get_data()
    amount = Decimal(data["payout_amount"])
    await state.clear()
    try:
        await payout_service.request_payout(account_id=data["account_id"], amount=amount, wallet_address=wallet)
    except ValueError as e:
        await message.answer(str(e))
        return
    await message.answer_photo(
        FSInputFile(_FINANCE_IMAGE),
        caption=f"<b><blockquote>💰 Финансы</blockquote>\n\n✅ Заявка на вывод <b>${amount:.2f}</b> отправлена!</b>",
        reply_markup=payout_menu_kb(has_available=False),
    )
