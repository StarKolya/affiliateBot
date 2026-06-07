from tortoise import fields
from tortoise.models import Model


class MarketingMessage(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, default="")
    # text | photo | video | animation | sticker | document | audio | voice
    content_type = fields.CharField(max_length=20)
    # Source of the original message — used for copy_message() broadcast
    source_chat_id = fields.BigIntField()
    source_message_id = fields.IntField()
    # Plain text/caption for admin preview only (no formatting)
    text = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    sent_at = fields.DatetimeField(null=True)
    sent_count = fields.IntField(default=0)

    class Meta:
        table = "marketing_messages"

    def __str__(self) -> str:
        return f"MarketingMessage(id={self.id}, type={self.content_type})"
