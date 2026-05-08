from tortoise import fields
from tortoise.models import Model


class Referral(Model):
    id = fields.IntField(pk=True)
    account: fields.ForeignKeyRelation = fields.ForeignKeyField(
        "models.Account", related_name="referrals", on_delete=fields.CASCADE
    )
    job_posting: fields.ForeignKeyNullableRelation = fields.ForeignKeyField(
        "models.JobPosting", related_name="referrals", on_delete=fields.SET_NULL, null=True
    )
    name = fields.CharField(max_length=50)
    # Unique slug used in /start?ref=<code>
    code = fields.CharField(max_length=50, unique=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "referrals"

    def __str__(self) -> str:
        return f"Referral(code={self.code})"


class ReferralEarning(Model):
    """
    Created once per (referral, application) pair when a trigger status is reached.
    The unique_together constraint enforces idempotency at the DB level.
    """

    id = fields.IntField(pk=True)
    referral: fields.ForeignKeyRelation[Referral] = fields.ForeignKeyField(
        "models.Referral", related_name="earnings", on_delete=fields.CASCADE
    )
    application: fields.ForeignKeyRelation = fields.ForeignKeyField(
        "models.JobApplication", related_name="earnings", on_delete=fields.CASCADE
    )
    amount = fields.DecimalField(max_digits=10, decimal_places=2)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "referral_earnings"
        # DB-level idempotency guard: one earning per referral+application
        unique_together = (("referral", "application"),)
