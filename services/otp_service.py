# backend/services/otp_service.py
import random
import string
from datetime import datetime, timedelta, timezone
from config.settings import Config
from config.database import db_cursor


class OTPService:
    """Generates, stores and validates OTP codes."""

    @staticmethod
    def generate() -> str:
        return ''.join(random.choices(string.digits, k=Config.OTP_LENGTH))

    @staticmethod
    def save(email: str, code: str, purpose: str) -> None:
        """Invalidate previous codes for this email+purpose, then insert new one."""
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=Config.OTP_EXPIRY_MINUTES
        )
        with db_cursor(commit=True) as (_, cursor):
            cursor.execute(
                "UPDATE otp_codes SET used = 1 WHERE email = %s AND purpose = %s AND used = 0",
                (email, purpose),
            )
            cursor.execute(
                """INSERT INTO otp_codes (email, code, purpose, expires_at)
                   VALUES (%s, %s, %s, %s)""",
                (email, code, purpose, expires_at.strftime('%Y-%m-%d %H:%M:%S')),
            )

    @staticmethod
    def verify(email: str, code: str, purpose: str) -> bool:
        """
        Returns True and marks the code used if valid;
        returns False if not found, expired, or already used.
        """
        with db_cursor(commit=True) as (_, cursor):
            cursor.execute(
                """SELECT id FROM otp_codes
                   WHERE email = %s AND code = %s AND purpose = %s
                     AND expires_at > NOW() AND used = 0
                   ORDER BY created_at DESC LIMIT 1""",
                (email, code, purpose),
            )
            row = cursor.fetchone()
            if not row:
                return False
            cursor.execute(
                "UPDATE otp_codes SET used = 1 WHERE id = %s", (row['id'],)
            )
        return True
