from tortoise import fields
from tortoise.models import Model


class MarketingMessage(Model):
    id = fields.IntField(pk=True)
    # text | photo | video | animation | sticker | document | audio | voice
    content_type = fields.CharField(max_length=20)
    file_id = fields.CharField(max_length=256, null=True)
    text = fields.TextField(null=True)
    # JSON-serialised list of MessageEntity dicts (preserves bold, italic, etc.)
    entities_json = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    sent_at = fields.DatetimeField(null=True)
    sent_count = fields.IntField(default=0)

    class Meta:
        table = "marketing_messages"

    def __str__(self) -> str:
        return f"MarketingMessage(id={self.id}, type={self.content_type})"
