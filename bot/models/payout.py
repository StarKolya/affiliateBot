from tortoise import fields
from tortoise.models import Model


class PayoutRequest(Model):
    id = fields.IntField(pk=True)
    account: fields.ForeignKeyRelation = fields.ForeignKeyField(
        "models.Account", related_name="payout_requests", on_delete=fields.CASCADE
    )
    amount = fields.DecimalField(max_digits=10, decimal_places=2)
    wallet_address = fields.CharField(max_length=100, null=True)
    # "pending" | "approved" | "rejected"
    status = fields.CharField(max_length=15, default="pending")
    admin_note = fields.CharField(max_length=500, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "payout_requests"

    def __str__(self) -> str:
        return f"Payout(id={self.id}, status={self.status})"
