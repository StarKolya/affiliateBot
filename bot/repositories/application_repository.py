from typing import List, Optional

from bot.models.application import ApplicationStatus, JobAnswer, JobApplication
from bot.repositories.base import BaseRepository


class ApplicationStatusRepository(BaseRepository[ApplicationStatus]):
    model = ApplicationStatus

    async def get_by_name(self, name: str) -> Optional[ApplicationStatus]:
        return await ApplicationStatus.get_or_none(name=name)


class JobApplicationRepository(BaseRepository[JobApplication]):
    model = JobApplication

    async def get_by_account(self, account_id: int) -> List[JobApplication]:
        return await JobApplication.filter(account_id=account_id).prefetch_related("status", "job_posting")

    async def get_with_details(self, application_id: int) -> Optional[JobApplication]:
        return await JobApplication.get_or_none(id=application_id).prefetch_related(
            "status", "job_posting", "referral", "account",
            "answers__job_question__question",
        )

    async def get_all_with_details(self) -> List[JobApplication]:
        return await JobApplication.all().prefetch_related("status", "job_posting", "account")

    async def get_by_niche(self, niche_id: int) -> List[JobApplication]:
        return await JobApplication.filter(
            job_posting__niche_id=niche_id
        ).prefetch_related("status", "job_posting", "account")

    async def get_by_job(self, job_id: int) -> List[JobApplication]:
        return await JobApplication.filter(
            job_posting_id=job_id
        ).prefetch_related("status", "job_posting", "account", "answers")

    async def update_status(self, application: JobApplication, status: ApplicationStatus) -> JobApplication:
        application.status = status
        await application.save(update_fields=["status_id", "updated_at"])
        return application


class JobAnswerRepository(BaseRepository[JobAnswer]):
    model = JobAnswer

    async def bulk_create(self, answers: List[JobAnswer]) -> None:
        await JobAnswer.bulk_create(answers, ignore_conflicts=True)
