
-- set db version number --
PRAGMA user_version = 100;

BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS `admin` (
    `admin_uuid` CHAR(36) UNIQUE NOT NULL,
    `firstname` TEXT NOT NULL,
    `lastname` TEXT NOT NULL,
    `email` TEXT NOT NULL,
    `email_hash` CHAR(128) NOT NULL,
    `email_validated` INTEGER NOT NULL,
    `otp_token` TEXT DEFAULT NULL,
    `otp_expiration` CHAR(30) DEFAULT NULL,
    `password` CHAR(128) NOT NULL,
    `user_salt` CHAR(50) NOT NULL,
    `last_login` CHAR(30) DEFAULT NULL,
    `creator_id` CHAR(36) NOT NULL,
    `created_date` CHAR(30) NOT NULL,
    `updated_date` CHAR(30) DEFAULT NULL,
    `deactivated` INTEGER NOT NULL,
    `deactivated_date` CHAR(30) DEFAULT NULL,
    PRIMARY KEY(`admin_uuid`)
);
