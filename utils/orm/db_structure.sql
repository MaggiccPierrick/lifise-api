
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
    `totp_url` TEXT DEFAULT NULL,
    `totp_base32` TEXT DEFAULT NULL,
    `totp_enabled` INTEGER NOT NULL DEFAULT 0,
    `creator_id` CHAR(36) NOT NULL,
    `created_date` CHAR(30) NOT NULL,
    `updated_date` CHAR(30) DEFAULT NULL,
    `deactivated` INTEGER NOT NULL,
    `deactivated_date` CHAR(30) DEFAULT NULL,
    PRIMARY KEY(`admin_uuid`)
);

CREATE TABLE IF NOT EXISTS `user_account` (
    `user_uuid` CHAR(36) UNIQUE NOT NULL,
    `firstname` TEXT DEFAULT NULL,
    `lastname` TEXT DEFAULT NULL,
    `birthdate` TEXT DEFAULT NULL,
    `email` TEXT NOT NULL,
    `email_hash` CHAR(128) UNIQUE NOT NULL,
    `email_validated` INTEGER NOT NULL,
    `selfie` CHAR(50) DEFAULT NULL,
    `otp_token` TEXT DEFAULT NULL,
    `otp_expiration` CHAR(30) DEFAULT NULL,
    `public_address` TEXT DEFAULT NULL,
    `magiclink_issuer` CHAR(60) UNIQUE DEFAULT NULL,
    `kyc_session_id` CHAR(36) UNIQUE DEFAULT NULL,
    `kyc_status` CHAR(30) DEFAULT NULL,
    `kyc_status_date` CHAR(30) DEFAULT NULL,
    `last_login` CHAR(30) DEFAULT NULL,
    `creator_id` CHAR(36) DEFAULT NULL,
    `created_date` CHAR(30) NOT NULL,
    `updated_date` CHAR(30) DEFAULT NULL,
    `deactivated` INTEGER NOT NULL,
    `deactivated_date` CHAR(30) DEFAULT NULL,
    PRIMARY KEY(`user_uuid`)
);

CREATE TABLE IF NOT EXISTS `beneficiary` (
    `beneficiary_uuid` CHAR(36) UNIQUE NOT NULL,
    `user_uuid` CHAR(36) NOT NULL,
    `beneficiary_user_uuid` CHAR(36) DEFAULT NULL,
    `public_address` TEXT DEFAULT NULL,
    `email` TEXT DEFAULT NULL,
    `created_date` CHAR(30) NOT NULL,
    `deactivated` INTEGER NOT NULL,
    `deactivated_date` CHAR(30) DEFAULT NULL,
    PRIMARY KEY(`beneficiary_uuid`),
    FOREIGN KEY(`user_uuid`) REFERENCES user_account(`user_uuid`),
    FOREIGN KEY(`beneficiary_user_uuid`) REFERENCES user_account(`user_uuid`)
);

CREATE TABLE IF NOT EXISTS `token_claim` (
    `token_claim_uuid` CHAR(36) UNIQUE NOT NULL,
    `user_uuid` CHAR(36) NOT NULL,
    `nb_token` FLOAT NOT NULL,
    `tx_hash` TEXT DEFAULT NULL,
    `creator_id` CHAR(36) DEFAULT NULL,
    `created_date` CHAR(30) NOT NULL,
    `claimed` INTEGER NOT NULL,
    `claimed_date` CHAR(30) DEFAULT NULL,
    `deactivated` INTEGER NOT NULL,
    `deactivated_date` CHAR(30) DEFAULT NULL,
    PRIMARY KEY(`token_claim_uuid`),
    FOREIGN KEY(`user_uuid`) REFERENCES user_account(`user_uuid`)
);

CREATE TABLE IF NOT EXISTS `user_purchase` (
    `user_purchase_uuid` CHAR(36) UNIQUE NOT NULL,
    `user_uuid` CHAR(36) NOT NULL,
    `nb_token` FLOAT NOT NULL,
    `total_price_eur` FLOAT NOT NULL,
    `reference` CHAR(20) NOT NULL,
    `amount_received` FLOAT DEFAULT NULL,
    `payment_date` CHAR(30) DEFAULT NULL,
    `tx_hash` TEXT DEFAULT NULL,
    `created_date` CHAR(30) NOT NULL,
    PRIMARY KEY(`user_purchase_uuid`),
    FOREIGN KEY(`user_uuid`) REFERENCES user_account(`user_uuid`)
);

CREATE TABLE IF NOT EXISTS `token_operation` (
    `token_operation_id` INTEGER NOT NULL AUTO_INCREMENT,
    `token_operation_uuid` CHAR(36) UNIQUE NOT NULL,
    `sender_uuid` CHAR(36) DEFAULT NULL,
    `receiver_uuid` CHAR(36) NOT NULL,
    `sender_address` CHAR(42) NOT NULL,
    `receiver_address` CHAR(42) NOT NULL,
    `token` CHAR(10) NOT NULL,
    `nb_token` FLOAT NOT NULL,
    `tx_hash` CHAR(66) DEFAULT NULL,
    `created_date` CHAR(30) NOT NULL,
    PRIMARY KEY(`token_operation_id`),
    FOREIGN KEY(`sender_uuid`) REFERENCES user_account(`user_uuid`),
    FOREIGN KEY(`receiver_uuid`) REFERENCES user_account(`user_uuid`)
);
