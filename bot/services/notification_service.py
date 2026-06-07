from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from bot.config import settings
from bot.models.application import JobApplication
from bot.utils.logger import get_logger

logger = get_logger(__name__)


async def notify_new_applicant(bot: Bot, application: JobApplication) -> None:
    """Send a notification to the configured channel when a new applicant arrives."""
    if not settings.APPLICANT_NOTIFICATIONS_CHANNEL_ID:
        return

    account = application.account
    job = application.job_posting

    name_parts = [account.name]
    if account.surname:
        name_parts.append(account.surname)
    full_name = " ".join(name_parts)

    username_line = f"@{account.username}" if account.username else "—"
    try:
        niche_name = job.niche.name if job.niche_id else "—"
    except Exception:
        niche_name = "—"

    lines = [
        "🆕 <b>Новый отклик!</b>",
        "",
        f"👤 <b>Имя:</b> {full_name}",
        f"🔗 <b>Username:</b> {username_line}",
        f"🪪 <b>Telegram ID:</b> <code>{account.telegram_id}</code>",
        f"💼 <b>Вакансия:</b> {job.title}",
        f"📁 <b>Ниша:</b> {niche_name}",
    ]

    answers = sorted(application.answers, key=lambda a: a.job_question_id)
    if answers:
        lines.append("")
        lines.append("📝 <b>Ответы:</b>")
        for ans in answers:
            q_text = ans.job_question.question.description if ans.job_question and ans.job_question.question else "—"
            lines.append(f"  • {q_text}: <i>{ans.answer}</i>")

    text = "\n".join(lines)

    try:
        await bot.send_message(settings.APPLICANT_NOTIFICATIONS_CHANNEL_ID, text)
    except TelegramAPIError as e:
        logger.error("Failed to send applicant notification: %s", e)
