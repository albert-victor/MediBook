-- mediBook Database Schema
-- Target: MySQL 8.0+
-- Charset: utf8mb4 | Collation: utf8mb4_unicode_ci
-- Generated from SQLAlchemy models - keep in sync via Alembic migrations

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ─────────────────────────────────────────────
-- users - authentication & identity
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    first_name      VARCHAR(100)  NOT NULL,
    last_name       VARCHAR(100)  NOT NULL,
    email           VARCHAR(255)  NOT NULL,
    phone           VARCHAR(20)   NULL,
    password_hash   VARCHAR(255)  NOT NULL,
    role            VARCHAR(20)   NOT NULL DEFAULT 'patient',
    is_active       TINYINT(1)    NOT NULL DEFAULT 1,
    created_at      DATETIME(6)   NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at      DATETIME(6)   NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    UNIQUE KEY uq_users_email (email),
    KEY ix_users_role (role),
    KEY ix_users_is_active (is_active),
    KEY ix_users_role_active (role, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────
-- specializations - lookup (no duplicated names)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS specializations (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(120)  NOT NULL,
    slug            VARCHAR(120)  NOT NULL,
    description     TEXT          NULL,
    icon            VARCHAR(60)   NULL,
    is_active       TINYINT(1)    NOT NULL DEFAULT 1,
    created_at      DATETIME(6)   NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at      DATETIME(6)   NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    UNIQUE KEY uq_specializations_name (name),
    UNIQUE KEY uq_specializations_slug (slug),
    KEY ix_specializations_name (name),
    KEY ix_specializations_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────
-- admins - profile extension for admin users
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS admins (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    user_id             INT          NOT NULL,
    department          VARCHAR(100) NOT NULL DEFAULT 'Operations',
    job_title           VARCHAR(100) NOT NULL DEFAULT 'Administrator',
    created_by_admin_id INT          NULL,
    created_at          DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at          DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    UNIQUE KEY uq_admins_user_id (user_id),
    KEY ix_admins_department (department),
    CONSTRAINT fk_admins_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_admins_created_by FOREIGN KEY (created_by_admin_id) REFERENCES admins (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────
-- doctors - profile extension for doctor users
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS doctors (
    id                    INT AUTO_INCREMENT PRIMARY KEY,
    user_id               INT            NOT NULL,
    specialization_id     INT            NOT NULL,
    license_number        VARCHAR(60)    NOT NULL,
    hospital_name         VARCHAR(200)   NOT NULL,
    bio                   TEXT           NULL,
    consultation_fee      DECIMAL(12,2)  NOT NULL,
    currency              VARCHAR(3)     NOT NULL DEFAULT 'TZS',
    experience_years      INT            NOT NULL DEFAULT 0,
    avatar_url            VARCHAR(500)   NULL,
    is_verified           TINYINT(1)     NOT NULL DEFAULT 0,
    is_accepting_patients TINYINT(1)     NOT NULL DEFAULT 1,
    created_at            DATETIME(6)    NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at            DATETIME(6)    NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    UNIQUE KEY uq_doctors_user_id (user_id),
    UNIQUE KEY uq_doctors_license_number (license_number),
    KEY ix_doctors_specialization_id (specialization_id),
    KEY ix_doctors_is_verified (is_verified),
    KEY ix_doctors_is_accepting (is_accepting_patients),
    CONSTRAINT fk_doctors_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_doctors_specialization_id FOREIGN KEY (specialization_id) REFERENCES specializations (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────
-- doctor_availability - bookable slots
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS doctor_availability (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    doctor_id   INT          NOT NULL,
    slot_start  DATETIME(6)  NOT NULL,
    slot_end    DATETIME(6)  NOT NULL,
    status      VARCHAR(20)  NOT NULL DEFAULT 'available',
    created_at  DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at  DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    UNIQUE KEY uq_doctor_availability_slot (doctor_id, slot_start),
    KEY ix_doctor_availability_doctor_id (doctor_id),
    KEY ix_doctor_availability_slot_start (slot_start),
    KEY ix_doctor_availability_status (status),
    KEY ix_doctor_availability_doctor_date (doctor_id, slot_start),
    CONSTRAINT fk_doctor_availability_doctor_id FOREIGN KEY (doctor_id) REFERENCES doctors (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────
-- appointments
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS appointments (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    patient_id          INT          NOT NULL,
    doctor_id           INT          NOT NULL,
    availability_id     INT          NULL,
    scheduled_start     DATETIME(6)  NOT NULL,
    scheduled_end       DATETIME(6)  NOT NULL,
    status              VARCHAR(20)  NOT NULL DEFAULT 'pending',
    patient_notes       TEXT         NULL,
    cancellation_reason TEXT         NULL,
    cancelled_at        DATETIME(6)  NULL,
    created_at          DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at          DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    UNIQUE KEY uq_appointment_doctor_slot (doctor_id, scheduled_start),
    UNIQUE KEY uq_appointment_availability (availability_id),
    KEY ix_appointments_patient_id (patient_id),
    KEY ix_appointments_doctor_id (doctor_id),
    KEY ix_appointments_status (status),
    KEY ix_appointments_scheduled_start (scheduled_start),
    KEY ix_appointments_patient_status (patient_id, status),
    CONSTRAINT fk_appointments_patient_id FOREIGN KEY (patient_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_appointments_doctor_id FOREIGN KEY (doctor_id) REFERENCES doctors (id) ON DELETE RESTRICT,
    CONSTRAINT fk_appointments_availability_id FOREIGN KEY (availability_id) REFERENCES doctor_availability (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────
-- appointment_status_history - audit trail
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS appointment_status_history (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id      INT          NOT NULL,
    status              VARCHAR(20)  NOT NULL,
    changed_by_user_id  INT          NULL,
    notes               TEXT         NULL,
    created_at          DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at          DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    KEY ix_appointment_status_history_appointment_id (appointment_id),
    KEY ix_appointment_status_history_status (status),
    KEY ix_appointment_status_history_changed_by (changed_by_user_id),
    CONSTRAINT fk_ash_appointment_id FOREIGN KEY (appointment_id) REFERENCES appointments (id) ON DELETE CASCADE,
    CONSTRAINT fk_ash_changed_by_user_id FOREIGN KEY (changed_by_user_id) REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────
-- payments - one per appointment
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS payments (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id    INT            NOT NULL,
    amount            DECIMAL(12,2)  NOT NULL,
    currency          VARCHAR(3)     NOT NULL DEFAULT 'TZS',
    payment_method    VARCHAR(30)    NOT NULL DEFAULT 'mpesa',
    status            VARCHAR(20)    NOT NULL DEFAULT 'pending',
    reference_number  VARCHAR(64)    NOT NULL,
    phone_number      VARCHAR(20)    NULL,
    failure_reason    TEXT           NULL,
    paid_at           DATETIME(6)    NULL,
    created_at        DATETIME(6)    NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at        DATETIME(6)    NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    UNIQUE KEY uq_payments_appointment (appointment_id),
    UNIQUE KEY uq_payments_reference (reference_number),
    KEY ix_payments_status (status),
    KEY ix_payments_method (payment_method),
    KEY ix_payments_paid_at (paid_at),
    CONSTRAINT fk_payments_appointment_id FOREIGN KEY (appointment_id) REFERENCES appointments (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────
-- notifications
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notifications (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    user_id           INT          NOT NULL,
    appointment_id    INT          NULL,
    notification_type VARCHAR(40)  NOT NULL DEFAULT 'general',
    channel           VARCHAR(20)  NOT NULL DEFAULT 'web',
    title             VARCHAR(200) NOT NULL,
    message           TEXT         NOT NULL,
    is_read           TINYINT(1)   NOT NULL DEFAULT 0,
    sent_at           DATETIME(6)  NULL,
    read_at           DATETIME(6)  NULL,
    created_at        DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at        DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    KEY ix_notifications_user_id (user_id),
    KEY ix_notifications_appointment_id (appointment_id),
    KEY ix_notifications_type (notification_type),
    KEY ix_notifications_is_read (is_read),
    KEY ix_notifications_user_unread (user_id, is_read),
    CONSTRAINT fk_notifications_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_notifications_appointment_id FOREIGN KEY (appointment_id) REFERENCES appointments (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────
-- password_reset_tokens
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT          NOT NULL,
    token       VARCHAR(128) NOT NULL,
    expires_at  DATETIME(6)  NOT NULL,
    used_at     DATETIME(6)  NULL,
    created_at  DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at  DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    UNIQUE KEY uq_password_reset_tokens_token (token),
    KEY ix_password_reset_tokens_token (token),
    CONSTRAINT fk_password_reset_tokens_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
