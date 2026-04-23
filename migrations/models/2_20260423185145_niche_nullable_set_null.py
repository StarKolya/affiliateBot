from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `job_postings` MODIFY COLUMN `niche_id` INT;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `job_postings` MODIFY COLUMN `niche_id` INT NOT NULL;"""


MODELS_STATE = (
    "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"
    "zAgG5+XOa6leTfz4H8f9V5A="
)
