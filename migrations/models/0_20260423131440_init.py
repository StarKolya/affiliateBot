from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `roles` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(50) NOT NULL UNIQUE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `accounts` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `telegram_id` BIGINT NOT NULL UNIQUE,
    `name` VARCHAR(100) NOT NULL,
    `surname` VARCHAR(100),
    `username` VARCHAR(50),
    `referred_by_code` VARCHAR(50),
    `subscription_verified` BOOL NOT NULL  DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `role_id` INT NOT NULL,
    CONSTRAINT `fk_accounts_roles_6681e4f3` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='Telegram user. telegram_id is the natural identity; id is internal PK.';
CREATE TABLE IF NOT EXISTS `niches` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(50) NOT NULL UNIQUE
) CHARACTER SET utf8mb4 COMMENT='Top-level category / area (was JobLabel in original SQL).';
CREATE TABLE IF NOT EXISTS `job_postings` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `title` VARCHAR(200) NOT NULL,
    `description` LONGTEXT,
    `status` VARCHAR(15) NOT NULL  DEFAULT 'active',
    `type` VARCHAR(15) NOT NULL,
    `commission` DECIMAL(8,2) NOT NULL  DEFAULT 0,
    `commission_secondary` DECIMAL(8,2),
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `niche_id` INT NOT NULL,
    CONSTRAINT `fk_job_post_niches_9637ad24` FOREIGN KEY (`niche_id`) REFERENCES `niches` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `questions` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `description` VARCHAR(500) NOT NULL,
    `expected_answer_type` VARCHAR(10) NOT NULL  DEFAULT 'text'
) CHARACTER SET utf8mb4 COMMENT='Predefined question bank. Questions are never job-specific until assigned.';
CREATE TABLE IF NOT EXISTS `job_questions` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `order` SMALLINT NOT NULL  DEFAULT 0,
    `job_posting_id` INT NOT NULL,
    `question_id` INT NOT NULL,
    UNIQUE KEY `uid_job_questio_job_pos_4dae57` (`job_posting_id`, `question_id`),
    CONSTRAINT `fk_job_ques_job_post_7317f0d1` FOREIGN KEY (`job_posting_id`) REFERENCES `job_postings` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_job_ques_question_3545ba33` FOREIGN KEY (`question_id`) REFERENCES `questions` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='M2M join: which questions are assigned to a specific job posting.';
CREATE TABLE IF NOT EXISTS `application_statuses` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(30) NOT NULL UNIQUE
) CHARACTER SET utf8mb4 COMMENT='Lookup table – seed with: Not accepted / Processing / Bought training / Joined team.';
CREATE TABLE IF NOT EXISTS `referrals` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(50) NOT NULL,
    `code` VARCHAR(50) NOT NULL UNIQUE,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `account_id` INT NOT NULL,
    CONSTRAINT `fk_referral_accounts_aaf37e1e` FOREIGN KEY (`account_id`) REFERENCES `accounts` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `job_applications` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `account_id` INT NOT NULL,
    `job_posting_id` INT NOT NULL,
    `referral_id` INT,
    `status_id` INT NOT NULL,
    CONSTRAINT `fk_job_appl_accounts_79e0c3dc` FOREIGN KEY (`account_id`) REFERENCES `accounts` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_job_appl_job_post_d3ed0d0f` FOREIGN KEY (`job_posting_id`) REFERENCES `job_postings` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_job_appl_referral_33b81a7e` FOREIGN KEY (`referral_id`) REFERENCES `referrals` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_job_appl_applicat_a23c602b` FOREIGN KEY (`status_id`) REFERENCES `application_statuses` (`id`) ON DELETE RESTRICT
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `job_answers` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `answer` VARCHAR(1000) NOT NULL,
    `application_id` INT NOT NULL,
    `job_question_id` INT NOT NULL,
    UNIQUE KEY `uid_job_answers_applica_745eab` (`application_id`, `job_question_id`),
    CONSTRAINT `fk_job_answ_job_appl_d924bf59` FOREIGN KEY (`application_id`) REFERENCES `job_applications` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_job_answ_job_ques_ae707ec9` FOREIGN KEY (`job_question_id`) REFERENCES `job_questions` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `referral_earnings` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `amount` DECIMAL(10,2) NOT NULL,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `application_id` INT NOT NULL,
    `referral_id` INT NOT NULL,
    UNIQUE KEY `uid_referral_ea_referra_b445e8` (`referral_id`, `application_id`),
    CONSTRAINT `fk_referral_job_appl_6c1acc2b` FOREIGN KEY (`application_id`) REFERENCES `job_applications` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_referral_referral_81af44eb` FOREIGN KEY (`referral_id`) REFERENCES `referrals` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='Created once per (referral, application) pair when a trigger status is reached.';
CREATE TABLE IF NOT EXISTS `payout_requests` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `amount` DECIMAL(10,2) NOT NULL,
    `status` VARCHAR(15) NOT NULL  DEFAULT 'pending',
    `admin_note` VARCHAR(500),
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `account_id` INT NOT NULL,
    CONSTRAINT `fk_payout_r_accounts_30948583` FOREIGN KEY (`account_id`) REFERENCES `accounts` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
    "XyZ+/h8HlPgr"
)
