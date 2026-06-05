from tortoise import fields
from tortoise.models import Model


class Role(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=50, unique=True)

    class Meta:
        table = "roles"

    def __str__(self) -> str:
        return self.name


class Account(Model):
    id = fields.IntField(pk=True)
    telegram_id = fields.BigIntField(unique=True)
    name = fields.CharField(max_length=100)
    surname = fields.CharField(max_length=100, null=True)
    username = fields.CharField(max_length=50, null=True)
    role: fields.ForeignKeyRelation[Role] = fields.ForeignKeyField(
        "models.Role", related_name="accounts", on_delete=fields.CASCADE
    )
    referred_by_code = fields.CharField(max_length=50, null=True)
    subscription_verified = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "accounts"

    def __str__(self) -> str:
        return f"Account(tg={self.telegram_id}, name={self.name})"
