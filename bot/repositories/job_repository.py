from typing import List, Optional

from bot.models.job import JobPosting, JobQuestion, Niche, Question
from bot.repositories.base import BaseRepository


class NicheRepository(BaseRepository[Niche]):
    model = Niche

    async def get_active_niches(self) -> List[Niche]:
        return await Niche.filter(job_postings__status="active").distinct()


class JobPostingRepository(BaseRepository[JobPosting]):
    model = JobPosting

    async def get_by_niche(self, niche_id: int) -> List[JobPosting]:
        return await JobPosting.filter(niche_id=niche_id, status="active")

    async def get_all_by_niche(self, niche_id: int) -> List[JobPosting]:
        return await JobPosting.filter(niche_id=niche_id)

    async def count_by_niche(self, niche_id: int) -> int:
        return await JobPosting.filter(niche_id=niche_id).count()

    async def get_with_questions(self, job_id: int) -> Optional[JobPosting]:
        return await JobPosting.get_or_none(id=job_id).prefetch_related(
            "job_questions__question"
        )


class QuestionRepository(BaseRepository[Question]):
    model = Question


class JobQuestionRepository(BaseRepository[JobQuestion]):
    model = JobQuestion

    async def get_by_job(self, job_id: int) -> List[JobQuestion]:
        return await JobQuestion.filter(job_posting_id=job_id).order_by("order").prefetch_related(
            "question"
        )

    async def assign_question(self, job_id: int, question_id: int, order: int = 0) -> JobQuestion:
        obj, _ = await JobQuestion.get_or_create(
            job_posting_id=job_id,
            question_id=question_id,
            defaults={"order": order},
        )
        return obj

    async def remove_question(self, job_id: int, question_id: int) -> None:
        await JobQuestion.filter(job_posting_id=job_id, question_id=question_id).delete()
