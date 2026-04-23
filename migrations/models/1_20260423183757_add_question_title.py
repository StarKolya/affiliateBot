from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `questions` ADD `title` VARCHAR(100) NOT NULL DEFAULT 'Untitled';
        ALTER TABLE `questions` ALTER COLUMN `title` DROP DEFAULT;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `questions` DROP COLUMN `title`;"""


MODELS_STATE = (
    "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"
    "qV9N/PgfBJ1YDg=="
)
