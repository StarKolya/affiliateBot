from tortoise import fields
from tortoise.models import Model


class Niche(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=50, unique=True)

    class Meta:
        table = "niches"

    def __str__(self) -> str:
        return self.name


class JobPosting(Model):
    id = fields.IntField(pk=True)
    niche: fields.ForeignKeyRelation[Niche] = fields.ForeignKeyField(
        "models.Niche", related_name="job_postings", on_delete=fields.SET_NULL, null=True
    )
    title = fields.CharField(max_length=200)
    description = fields.TextField(null=True)
    # e.g. "active" | "paused" | "closed"
    status = fields.CharField(max_length=15, default="active")
    # e.g. "full-time" | "part-time" | "contract"
    type = fields.CharField(max_length=15)
    # Primary commission: Deal Closed (partnership) / Joined Team (offer)
    commission = fields.DecimalField(max_digits=8, decimal_places=2, default=0)
    # Secondary commission: Bought Course (offer only)
    commission_secondary = fields.DecimalField(max_digits=8, decimal_places=2, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "job_postings"

    def __str__(self) -> str:
        return self.title


class Question(Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=100)
    description = fields.CharField(max_length=500)
    # Expected answer type hint: "text" | "yes_no" | "number"
    expected_answer_type = fields.CharField(max_length=10, default="text")

    class Meta:
        table = "questions"

    def __str__(self) -> str:
        return self.title


class JobQuestion(Model):

    id = fields.IntField(pk=True)
    job_posting: fields.ForeignKeyRelation[JobPosting] = fields.ForeignKeyField(
        "models.JobPosting", related_name="job_questions", on_delete=fields.CASCADE
    )
    question: fields.ForeignKeyRelation[Question] = fields.ForeignKeyField(
        "models.Question", related_name="job_questions", on_delete=fields.CASCADE
    )
    order = fields.SmallIntField(default=0)

    class Meta:
        table = "job_questions"
        unique_together = (("job_posting", "question"),)
