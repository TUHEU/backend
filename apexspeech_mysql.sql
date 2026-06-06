-- ============================================================
--  APEX SPEECH  —  MySQL Database
--  Run:  mysql -u root -p < database/apexspeech_mysql.sql
-- ============================================================

DROP DATABASE IF EXISTS apexspeech_db;
CREATE DATABASE apexspeech_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE apexspeech_db;

-- ── users ────────────────────────────────────────────────────
CREATE TABLE users (
  id             INT UNSIGNED   NOT NULL AUTO_INCREMENT,
  username       VARCHAR(100)   NOT NULL,
  email          VARCHAR(150)   NOT NULL,
  password_hash  VARCHAR(255)   NOT NULL,
  full_name      VARCHAR(150)   DEFAULT NULL,
  goal           TEXT           DEFAULT NULL,
  total_sessions INT UNSIGNED   NOT NULL DEFAULT 0,
  avg_speed      FLOAT          NOT NULL DEFAULT 0.0,
  avg_fillers    FLOAT          NOT NULL DEFAULT 0.0,
  is_active      TINYINT(1)     NOT NULL DEFAULT 1,
  created_at     DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_email    (email),
  UNIQUE KEY uq_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── recordings ───────────────────────────────────────────────
CREATE TABLE recordings (
  id                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id             INT UNSIGNED DEFAULT NULL,
  title               VARCHAR(200) NOT NULL,
  audio_path          VARCHAR(500) NOT NULL,
  transcript          TEXT         DEFAULT NULL,
  word_count          INT UNSIGNED NOT NULL DEFAULT 0,
  filler_word_count   INT UNSIGNED NOT NULL DEFAULT 0,
  repeated_word_count INT UNSIGNED NOT NULL DEFAULT 0,
  speaking_speed      FLOAT        NOT NULL DEFAULT 0.0,
  frequent_words      TEXT         DEFAULT NULL,
  ai_feedback         TEXT         DEFAULT NULL,
  ai_score            TINYINT UNSIGNED DEFAULT NULL,
  duration_seconds    INT UNSIGNED NOT NULL DEFAULT 0,
  date_created        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_user_id (user_id),
  INDEX idx_created (date_created),
  CONSTRAINT fk_rec_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── seed: demo user  (password = Demo@1234) ──────────────────
INSERT INTO users (username, email, password_hash, full_name, goal)
VALUES (
  'demo_user',
  'demo@apexspeech.io',
  '$2b$12$KIX8Xe4b3SzKlf7YqD1mUeQwZ5vN2pT8rHjC0sA6dLmFyGnBuOiWe',
  'Demo User',
  'Reduce filler words and speak with more confidence'
);

-- ── seed: sample recording ────────────────────────────────────
INSERT INTO recordings (
  user_id, title, audio_path, transcript,
  word_count, filler_word_count, speaking_speed,
  ai_feedback, ai_score, date_created
) VALUES (
  1,
  'Session 2026-06-01 09:00',
  '/demo/sample_session.aac',
  'Hello everyone today I want to talk about um the importance of clear communication you know',
  16, 2, 128.0,
  '📊 OVERALL SCORE: 7 / 10\n\n✅ STRENGTHS\n• Clear topic introduction.\n• Good speaking speed.\n\n⚠️ FILLER WORDS (2 detected)\n• 2 filler words — good control!\n\n⏱️ SPEAKING SPEED\n• 128 WPM — ideal range!\n\n💡 3 TIPS\n1. Record daily.\n2. Pause after key points.\n3. Vary sentence length.',
  7,
  NOW()
);

SELECT CONCAT('✓ Database ready — ', COUNT(*), ' tables created') AS status
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'apexspeech_db';
