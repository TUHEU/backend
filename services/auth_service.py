# backend/services/auth_service.py
import random
import string
import bcrypt
import jwt
import uuid
from datetime import datetime, timedelta
from config.settings import Config
from config.database import db_cursor


class AuthService:
    """Handles all authentication business logic."""

    # ── Password helpers ──────────────────────────────────────

    @staticmethod
    def hash_password(plain: str) -> str:
        return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode(), hashed.encode())

    # ── JWT helpers ───────────────────────────────────────────

    @staticmethod
    def generate_access_token(user_id: int) -> str:
        payload = {
            'sub': user_id,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRY_HOURS),
            'type': 'access',
        }
        return jwt.encode(payload, Config.JWT_SECRET, algorithm='HS256')

    @staticmethod
    def generate_refresh_token(user_id: int) -> str:
        token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=Config.JWT_REFRESH_DAYS)
        with db_cursor(commit=True) as (_, cursor):
            cursor.execute(
                "INSERT INTO refresh_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)",
                (user_id, token, expires_at)
            )
        return token

    @staticmethod
    def verify_access_token(token: str) -> dict | None:
        try:
            return jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    # ── OTP helpers ───────────────────────────────────────────

    @staticmethod
    def generate_otp(email: str, purpose: str) -> str:
        code = ''.join(random.choices(string.digits, k=Config.OTP_LENGTH))
        expires_at = datetime.utcnow() + timedelta(minutes=Config.OTP_EXPIRY_MINUTES)
        with db_cursor(commit=True) as (_, cursor):
            # Invalidate old codes for same email + purpose
            cursor.execute(
                "UPDATE otp_codes SET used=1 WHERE email=%s AND purpose=%s AND used=0",
                (email, purpose)
            )
            cursor.execute(
                "INSERT INTO otp_codes (email, code, purpose, expires_at) VALUES (%s, %s, %s, %s)",
                (email, code, purpose, expires_at)
            )
        return code

    @staticmethod
    def verify_otp(email: str, code: str, purpose: str) -> bool:
        with db_cursor(commit=True) as (_, cursor):
            cursor.execute(
                """SELECT id FROM otp_codes
                   WHERE email=%s AND code=%s AND purpose=%s
                     AND used=0 AND expires_at > UTC_TIMESTAMP()
                   ORDER BY created_at DESC LIMIT 1""",
                (email, code, purpose)
            )
            row = cursor.fetchone()
            if not row:
                return False
            cursor.execute("UPDATE otp_codes SET used=1 WHERE id=%s", (row['id'],))
            return True

    # ── User CRUD ─────────────────────────────────────────────

    @staticmethod
    def get_user_by_email(email: str) -> dict | None:
        with db_cursor() as (_, cursor):
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            return cursor.fetchone()

    @staticmethod
    def get_user_by_id(user_id: int) -> dict | None:
        with db_cursor() as (_, cursor):
            cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
            return cursor.fetchone()

    @staticmethod
    def create_user(full_name: str, email: str, phone: str,
                    password_hash: str, date_of_birth: str | None,
                    profile_image_url: str | None) -> int:
        with db_cursor(commit=True) as (_, cursor):
            cursor.execute(
                """INSERT INTO users
                   (full_name, email, phone, password_hash, date_of_birth, profile_image_url)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (full_name, email, phone, password_hash, date_of_birth, profile_image_url)
            )
            return cursor.lastrowid

    @staticmethod
    def mark_email_verified(email: str) -> None:
        with db_cursor(commit=True) as (_, cursor):
            cursor.execute(
                "UPDATE users SET is_email_verified=1 WHERE email=%s", (email,)
            )

    @staticmethod
    def update_password(email: str, new_hash: str) -> None:
        with db_cursor(commit=True) as (_, cursor):
            cursor.execute(
                "UPDATE users SET password_hash=%s WHERE email=%s", (new_hash, email)
            )

    @staticmethod
    def update_profile(user_id: int, data: dict) -> None:
        allowed = ['full_name', 'phone', 'bio', 'job_title', 'company',
                   'date_of_birth', 'profile_image_url']
        fields = {k: v for k, v in data.items() if k in allowed and v is not None}
        if not fields:
            return
        set_clause = ', '.join(f"{k}=%s" for k in fields)
        with db_cursor(commit=True) as (_, cursor):
            cursor.execute(
                f"UPDATE users SET {set_clause} WHERE id=%s",
                (*fields.values(), user_id)
            )

    @staticmethod
    def revoke_refresh_token(token: str) -> None:
        with db_cursor(commit=True) as (_, cursor):
            cursor.execute("DELETE FROM refresh_tokens WHERE token=%s", (token,))

    # ── Serialisation ─────────────────────────────────────────

    @staticmethod
    def user_to_dict(user: dict) -> dict:
        """Strip sensitive fields before sending to client."""
        return {
            'id': user['id'],
            'full_name': user['full_name'],
            'email': user['email'],
            'phone': user.get('phone'),
            'date_of_birth': str(user['date_of_birth']) if user.get('date_of_birth') else None,
            'profile_image_url': user.get('profile_image_url'),
            'is_email_verified': bool(user.get('is_email_verified')),
            'bio': user.get('bio'),
            'job_title': user.get('job_title'),
            'company': user.get('company'),
            'created_at': str(user['created_at']) if user.get('created_at') else None,
        }
