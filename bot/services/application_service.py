from typing import Dict, List, Optional

from bot.models.application import ApplicationStatus, JobApplication
from bot.repositories.application_repository import (
    ApplicationStatusRepository,
    JobAnswerRepository,
    JobApplicationRepository,
)
from bot.exceptions import AlreadyAppliedException
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
        raise AlreadyAppliedException(account_id, job_id)

    processing = await status_repo.get_by_name("Pending")
    if processing is None:
        raise RuntimeError("ApplicationStatus 'Pending' missing — run seed_initial_data()")

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
    from bot.services import referral_service

    application = await app_repo.get_with_details(application_id)
    if application is None:
        raise ValueError(f"Application {application_id} not found")

    new_status = await status_repo.get_by_name(new_status_name)
    if new_status is None:
        raise ValueError(f"Unknown status: {new_status_name}")

    application = await app_repo.update_status(application, new_status)

    if application.referral_id:
        await referral_service.maybe_create_earning(
            application_id=application.id,
            referral_id=application.referral_id,
            new_status_name=new_status_name,
            job_type=application.job_posting.type,
            commission=application.job_posting.commission,
            commission_secondary=application.job_posting.commission_secondary,
        )

    logger.info("Application %s status → %s", application_id, new_status_name)
    return application


async def get_application(application_id: int) -> Optional[JobApplication]:
    return await app_repo.get_with_details(application_id)


async def list_all_applications() -> List[JobApplication]:
    return await app_repo.get_all_with_details()


async def list_applications_by_niche(niche_id: int) -> List[JobApplication]:
    return await app_repo.get_by_niche(niche_id)


async def list_applications_by_job(job_id: int) -> List[JobApplication]:
    return await app_repo.get_by_job(job_id)


def apply_numeric_filters(
    applications: List[JobApplication],
    filters: Dict[int, float],
) -> List[JobApplication]:
    """Filter applications in-memory by minimum value per job_question_id."""
    if not filters:
        return applications
    result = []
    for app in applications:
        match = True
        for jq_id, min_val in filters.items():
            answer = next((a for a in app.answers if a.job_question_id == jq_id), None)
            if answer is None:
                match = False
                break
            try:
                if float(answer.answer) < min_val:
                    match = False
                    break
            except ValueError:
                match = False
                break
        if match:
            result.append(app)
    return result


async def list_user_applications(account_id: int) -> List[JobApplication]:
    return await app_repo.get_by_account(account_id)
