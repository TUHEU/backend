# backend/config/database.py
import pymysql
import pymysql.cursors
from contextlib import contextmanager
from config.settings import Config


def get_connection():
    """Return a new PyMySQL connection."""
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASS,
        database=Config.DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


@contextmanager
def db_cursor(commit: bool = False):
    """
    Context manager that yields (connection, cursor).
    Commits on success if commit=True, rolls back on error.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            yield conn, cursor
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create all tables if they do not exist."""
    ddl_statements = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id               INT AUTO_INCREMENT PRIMARY KEY,
            full_name        VARCHAR(120)  NOT NULL,
            email            VARCHAR(255)  NOT NULL UNIQUE,
            phone            VARCHAR(30),
            password_hash    VARCHAR(255)  NOT NULL,
            date_of_birth    DATE,
            profile_image_url TEXT,
            is_email_verified TINYINT(1)   NOT NULL DEFAULT 0,
            bio              TEXT,
            job_title        VARCHAR(120),
            company          VARCHAR(120),
            created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_email (email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS otp_codes (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            email      VARCHAR(255) NOT NULL,
            code       VARCHAR(10)  NOT NULL,
            purpose    ENUM('email_verification','password_reset') NOT NULL,
            expires_at DATETIME     NOT NULL,
            used       TINYINT(1)   NOT NULL DEFAULT 0,
            created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_email_purpose (email, purpose)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            user_id    INT          NOT NULL,
            token      VARCHAR(512) NOT NULL UNIQUE,
            expires_at DATETIME     NOT NULL,
            created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_token (token)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS job_listings (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            title       VARCHAR(200) NOT NULL,
            company     VARCHAR(200) NOT NULL,
            location    VARCHAR(200),
            job_type    ENUM('Full-time','Part-time','Remote','Internship','Contract') DEFAULT 'Full-time',
            salary_min  DECIMAL(10,2),
            salary_max  DECIMAL(10,2),
            description TEXT,
            requirements TEXT,
            is_active   TINYINT(1) DEFAULT 1,
            created_at  DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_active (is_active),
            INDEX idx_type (job_type)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS job_applications (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            user_id      INT NOT NULL,
            job_id       INT NOT NULL,
            status       ENUM('applied','reviewed','interview','offer','rejected') DEFAULT 'applied',
            applied_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (job_id)  REFERENCES job_listings(id) ON DELETE CASCADE,
            UNIQUE KEY uq_user_job (user_id, job_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS saved_jobs (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            user_id    INT NOT NULL,
            job_id     INT NOT NULL,
            saved_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (job_id)  REFERENCES job_listings(id) ON DELETE CASCADE,
            UNIQUE KEY uq_saved (user_id, job_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS ai_conversations (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            user_id    INT NOT NULL,
            role       ENUM('user','assistant') NOT NULL,
            content    TEXT NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_user_time (user_id, created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS community_posts (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            user_id    INT NOT NULL,
            content    TEXT NOT NULL,
            likes      INT  NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
    ]
    with db_cursor(commit=True) as (conn, cursor):
        for stmt in ddl_statements:
            cursor.execute(stmt)
    print("[DB] All tables initialised.")
