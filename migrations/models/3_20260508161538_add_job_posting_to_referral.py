from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `referrals` ADD `job_posting_id` INT;
        ALTER TABLE `referrals` ADD CONSTRAINT `fk_referral_job_post_e1bae01e` FOREIGN KEY (`job_posting_id`) REFERENCES `job_postings` (`id`) ON DELETE SET NULL;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `referrals` DROP FOREIGN KEY `fk_referral_job_post_e1bae01e`;
        ALTER TABLE `referrals` DROP COLUMN `job_posting_id`;"""


MODELS_STATE = (
    "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"
)
