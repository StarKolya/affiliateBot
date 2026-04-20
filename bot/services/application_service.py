from typing import Dict, List, Optional

from bot.models.application import ApplicationStatus, JobApplication
from bot.repositories.application_repository import (
    ApplicationStatusRepository,
    JobAnswerRepository,
    JobApplicationRepository,
)
from bot.utils.logger import get_logger

logger = get_logger(__name__)

app_repo = JobApplicationRepository()
status_repo = ApplicationStatusRepository()
answer_repo = JobAnswerRepository()


async def start_application(
    account_id: int,
    job_id: int,
    referral_id: Optional[int],
) -> JobApplication:
    """Create a new application in default 'Processing' status."""
    ...


async def submit_answers(application_id: int, answers: Dict[int, str]) -> None:
    """Persist answers keyed by JobQuestion.id."""
    ...


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
