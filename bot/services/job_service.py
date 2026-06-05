from typing import List, Optional

from bot.models.job import JobPosting, JobQuestion, Niche, Question


def sort_jobs_by_commission(jobs: List[JobPosting]) -> List[JobPosting]:
    """Return jobs sorted by primary commission descending (highest paying first)."""
    return sorted(jobs, key=lambda j: float(j.commission), reverse=True)
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
    return await niche_repo.get_active_niches()


async def list_jobs_by_niche(niche_id: int) -> List[JobPosting]:
    jobs = await job_repo.get_by_niche(niche_id)
    return sort_jobs_by_commission(jobs)


async def get_job(job_id: int) -> Optional[JobPosting]:
    return await job_repo.get_by_id(job_id)


async def get_job_with_questions(job_id: int) -> Optional[JobPosting]:
    return await job_repo.get_with_questions(job_id)


async def list_all_niches() -> List[Niche]:
    return await niche_repo.get_all()


async def get_niche(niche_id: int) -> Optional[Niche]:
    return await niche_repo.get_by_id(niche_id)


async def create_niche(name: str) -> Niche:
    return await niche_repo.create(name=name)


async def count_jobs_by_niche(niche_id: int) -> int:
    return await job_repo.count_by_niche(niche_id)


async def list_all_jobs_by_niche(niche_id: int) -> List[JobPosting]:
    return await job_repo.get_all_by_niche(niche_id)


async def delete_niche(niche_id: int) -> None:
    jobs = await job_repo.get_all_by_niche(niche_id)
    for job in jobs:
        await job_repo.update(job, status="closed")
    niche = await niche_repo.get_by_id(niche_id)
    await niche_repo.delete(niche)


async def set_job_status(job_id: int, status: str) -> JobPosting:
    job = await job_repo.get_by_id(job_id)
    return await job_repo.update(job, status=status)


async def list_all_questions() -> List[Question]:
    return await question_repo.get_all()


async def create_job_posting(
    niche_id: int,
    title: str,
    job_type: str,
    commission: float,
    commission_secondary: float | None = None,
    description: str | None = None,
) -> JobPosting:
    return await job_repo.create(
        niche_id=niche_id,
        title=title,
        type=job_type,
        commission=commission,
        commission_secondary=commission_secondary,
        description=description,
        status="active",
    )


async def delete_job_posting(job_id: int) -> None:
    ...


async def assign_question_to_job(job_id: int, question_id: int, order: int = 0) -> JobQuestion:
    return await job_question_repo.assign_question(job_id, question_id, order)


async def remove_question_from_job(job_id: int, question_id: int) -> None:
    ...
