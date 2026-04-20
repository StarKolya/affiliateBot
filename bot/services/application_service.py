from typing import Dict, List, Optional

from bot.models.application import ApplicationStatus, JobApplication
from bot.repositories.application_repository import (
    ApplicationStatusRepository,
    JobAnswerRepository,
    JobApplicationRepository,
)
from bot.repositories.referral_repository import ReferralRepository
from bot.utils.logger import get_logger

logger = get_logger(__name__)

app_repo = JobApplicationRepository()
status_repo = ApplicationStatusRepository()
answer_repo = JobAnswerRepository()
referral_repo = ReferralRepository()


async def start_application(
    account_id: int,
    job_id: int,
    referred_by_code: Optional[str] = None,
) -> JobApplication:
    """Create a new application in default 'Processing' status."""
    already = await app_repo.model.filter(account_id=account_id, job_posting_id=job_id).exists()
    if already:
        raise ValueError("already_applied")

    processing = await status_repo.get_by_name("Processing")
    if processing is None:
        raise RuntimeError("ApplicationStatus 'Processing' missing — run seed_initial_data()")

    referral_id: Optional[int] = None
    if referred_by_code:
        referral = await referral_repo.get_by_code(referred_by_code)
        if referral:
            referral_id = referral.id

    return await app_repo.create(
        account_id=account_id,
        job_posting_id=job_id,
        status=processing,
        referral_id=referral_id,
    )


async def submit_answers(application_id: int, answers: Dict[int, str]) -> None:
    """Persist answers keyed by JobQuestion.id."""
    from bot.models.application import JobAnswer

    objects = [
        JobAnswer(application_id=application_id, job_question_id=qid, answer=text)
        for qid, text in answers.items()
    ]
    await answer_repo.bulk_create(objects)


async def update_application_status(
    application_id: int,
    new_status_name: str,
) -> JobApplication:
    """
    Change status and delegate earning creation to referral_service.
    Must be idempotent with respect to referral earnings.
    """
    ...


async def get_application(application_id: int) -> Optional[JobApplication]:
    ...


async def list_all_applications() -> List[JobApplication]:
    ...


async def list_user_applications(account_id: int) -> List[JobApplication]:
    ...
