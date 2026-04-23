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
    from bot.config import settings
    from bot.models.account import Account, Role
    from bot.models.application import ApplicationStatus

    for name in ("user", "admin"):
        await Role.get_or_create(name=name)

    for name in ("Pending", "Declined", "Deal Closed", "Joined Team", "Bought Course"):
        await ApplicationStatus.get_or_create(name=name)

    if settings.ADMIN_TELEGRAM_IDS:
        admin_role = await Role.get(name="admin")
        await Account.filter(telegram_id__in=settings.ADMIN_TELEGRAM_IDS).update(role=admin_role)


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
        defaults={"title": "Experience", "expected_answer_type": "text"},
    )
    q2, _ = await Question.get_or_create(
        description="Are you available to start immediately?",
        defaults={"title": "Availability", "expected_answer_type": "yes_no"},
    )
    q3, _ = await Question.get_or_create(
        description="What is your expected salary?",
        defaults={"title": "Expected Salary", "expected_answer_type": "number"},
    )

    # Job postings
    job1, _ = await JobPosting.get_or_create(
        title="Senior Recruiter",
        defaults={
            "niche": hr,
            "description": "We are looking for an experienced recruiter to join our HR team.",
            "type": "offer",
            "commission": 500,
            "commission_secondary": 200,
            "status": "active",
        },
    )
    job2, _ = await JobPosting.get_or_create(
        title="Python Developer",
        defaults={
            "niche": it,
            "description": "Join our backend team and build scalable Python services.",
            "type": "offer",
            "commission": 800,
            "commission_secondary": 300,
            "status": "active",
        },
    )
    job3, _ = await JobPosting.get_or_create(
        title="IT Partnership",
        defaults={
            "niche": it,
            "description": "Strategic partnership opportunity in the IT space.",
            "type": "partnership",
            "commission": 1500,
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
