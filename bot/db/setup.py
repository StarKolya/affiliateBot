from tortoise import Tortoise

from bot.config import settings

TORTOISE_ORM = {
    "connections": {
        "default": settings.db_url,
    },
    "apps": {
        "models": {
            "models": [
                "bot.models.account",
                "bot.models.job",
                "bot.models.application",
                "bot.models.referral",
                "bot.models.payout",
                "aerich.models",
            ],
            "default_connection": "default",
        }
    },
    "use_tz": True,
    "timezone": "UTC",
}


async def init_db() -> None:
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas(safe=True)


async def close_db() -> None:
    await Tortoise.close_connections()


async def seed_initial_data() -> None:
    """
    Idempotent seed for lookup tables that must exist before any business logic runs.
    Called once on startup after generate_schemas.
    """
    from bot.models.account import Role
    from bot.models.application import ApplicationStatus

    for name in ("user", "admin"):
        await Role.get_or_create(name=name)

    for name in ("Processing", "Not accepted", "Bought training", "Joined team"):
        await ApplicationStatus.get_or_create(name=name)


async def seed_test_data() -> None:
    """
    Idempotent seed for manual testing.
    Creates: 2 niches, 3 questions, 2 job postings, assigns questions to jobs.
    Safe to run multiple times.
    """
    from bot.models.job import JobPosting, JobQuestion, Niche, Question

    # Niches
    hr, _ = await Niche.get_or_create(name="HR")
    it, _ = await Niche.get_or_create(name="IT")

    # Question bank
    q1, _ = await Question.get_or_create(
        description="Tell us about your relevant experience.",
        defaults={"expected_answer_type": "text"},
    )
    q2, _ = await Question.get_or_create(
        description="Are you available to start immediately?",
        defaults={"expected_answer_type": "yes_no"},
    )
    q3, _ = await Question.get_or_create(
        description="What is your expected salary?",
        defaults={"expected_answer_type": "number"},
    )

    # Job postings
    job1, _ = await JobPosting.get_or_create(
        title="Senior Recruiter",
        defaults={
            "niche": hr,
            "description": "We are looking for an experienced recruiter to join our HR team.",
            "type": "full-time",
            "commission": 500,
            "status": "active",
        },
    )
    job2, _ = await JobPosting.get_or_create(
        title="Python Developer",
        defaults={
            "niche": it,
            "description": "Join our backend team and build scalable Python services.",
            "type": "full-time",
            "commission": 800,
            "status": "active",
        },
    )
    job3, _ = await JobPosting.get_or_create(
        title="Junior IT Support",
        defaults={
            "niche": it,
            "description": "First-line support role, great entry point into IT.",
            "type": "part-time",
            "commission": 200,
            "status": "active",
        },
    )

    # Assign questions to jobs (order matters)
    for job, questions in [
        (job1, [(q1, 0), (q2, 1)]),
        (job2, [(q1, 0), (q3, 1)]),
        (job3, [(q2, 0)]),
    ]:
        for question, order in questions:
            await JobQuestion.get_or_create(
                job_posting=job,
                question=question,
                defaults={"order": order},
            )
