from tortoise import fields
from tortoise.models import Model


class ApplicationStatus(Model):
    """Lookup table – seed with: Not accepted / Processing / Bought training / Joined team."""

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=30, unique=True)

    class Meta:
        table = "application_statuses"

    def __str__(self) -> str:
        return self.name


class JobApplication(Model):
    id = fields.IntField(pk=True)
    job_posting: fields.ForeignKeyRelation = fields.ForeignKeyField(
        "models.JobPosting", related_name="applications", on_delete=fields.CASCADE
    )
    account: fields.ForeignKeyRelation = fields.ForeignKeyField(
        "models.Account", related_name="applications", on_delete=fields.CASCADE
    )
    status: fields.ForeignKeyRelation[ApplicationStatus] = fields.ForeignKeyField(
        "models.ApplicationStatus", related_name="applications", on_delete=fields.RESTRICT
    )
    # Nullable: application may not come through a referral link
    referral: fields.ForeignKeyNullableRelation = fields.ForeignKeyField(
        "models.Referral", related_name="applications", null=True, on_delete=fields.SET_NULL
    )
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "job_applications"

    def __str__(self) -> str:
        return f"Application(id={self.id})"


class JobAnswer(Model):
    id = fields.IntField(pk=True)
    application: fields.ForeignKeyRelation[JobApplication] = fields.ForeignKeyField(
        "models.JobApplication", related_name="answers", on_delete=fields.CASCADE
    )
    job_question: fields.ForeignKeyRelation = fields.ForeignKeyField(
        "models.JobQuestion", related_name="answers", on_delete=fields.CASCADE
    )
    answer = fields.CharField(max_length=1000)

    class Meta:
        table = "job_answers"
        unique_together = (("application", "job_question"),)
