from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `marketing_messages` ADD `name` VARCHAR(100) NOT NULL DEFAULT '';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `marketing_messages` DROP COLUMN `name`;"""
