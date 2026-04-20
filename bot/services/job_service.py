from typing import List, Optional

from bot.models.job import JobPosting, JobQuestion, Niche, Question
from bot.repositories.job_repository import (
    JobPostingRepository,
    JobQuestionRepository,
    NicheRepository,
    QuestionRepository,
)
from bot.utils.logger import get_logger

logger = get_logger(__name__)

niche_repo = NicheRepository()
job_repo = JobPostingRepository()
question_repo = QuestionRepository()
job_question_repo = JobQuestionRepository()


async def list_active_niches() -> List[Niche]:
    ...


async def list_jobs_by_niche(niche_id: int) -> List[JobPosting]:
    ...


async def get_job_with_questions(job_id: int) -> Optional[JobPosting]:
    ...


async def list_all_questions() -> List[Question]:
    ...


async def create_job_posting(niche_id: int, title: str, type: str, commission: float) -> JobPosting:
    ...


async def delete_job_posting(job_id: int) -> None:
    ...


async def assign_question_to_job(job_id: int, question_id: int, order: int = 0) -> JobQuestion:
    ...


async def remove_question_from_job(job_id: int, question_id: int) -> None:
    ...
