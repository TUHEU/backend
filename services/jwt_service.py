# backend/services/jwt_service.py
import jwt
import uuid
from datetime import datetime, timedelta, timezone
from config.settings import Config
from config.database import db_cursor


class JWTService:
    """Handles creation and validation of access + refresh tokens."""

    @staticmethod
    def generate_access_token(user_id: int, email: str) -> str:
        payload = {
            'sub': user_id,
            'email': email,
            'iat': datetime.now(timezone.utc),
            'exp': datetime.now(timezone.utc) + timedelta(hours=Config.JWT_EXPIRY_HOURS),
            'type': 'access',
        }
        return jwt.encode(payload, Config.JWT_SECRET, algorithm='HS256')

    @staticmethod
    def generate_refresh_token(user_id: int) -> str:
        token = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(days=Config.JWT_REFRESH_DAYS)
        with db_cursor(commit=True) as (_, cursor):
            # Remove old tokens beyond 5 per user
            cursor.execute("""
                DELETE FROM refresh_tokens
                WHERE user_id = %s
                  AND id NOT IN (
                      SELECT id FROM (
                          SELECT id FROM refresh_tokens
                          WHERE user_id = %s
                          ORDER BY created_at DESC
                          LIMIT 4
                      ) AS t
                  )
            """, (user_id, user_id))
            cursor.execute(
                "INSERT INTO refresh_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)",
                (user_id, token, expires_at.strftime('%Y-%m-%d %H:%M:%S'))
            )
        return token

    @staticmethod
    def decode_access_token(token: str) -> dict:
        """Raises jwt.ExpiredSignatureError or jwt.InvalidTokenError on failure."""
        return jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])

    @staticmethod
    def revoke_refresh_token(token: str) -> bool:
        with db_cursor(commit=True) as (_, cursor):
            rows = cursor.execute(
                "DELETE FROM refresh_tokens WHERE token = %s", (token,)
            )
        return rows > 0

    @staticmethod
    def rotate_refresh_token(old_token: str) -> tuple[str, int] | None:
        """Validate old refresh token, delete it, issue a new one."""
        with db_cursor(commit=True) as (_, cursor):
            cursor.execute("""
                SELECT user_id FROM refresh_tokens
                WHERE token = %s AND expires_at > NOW() AND used = 0
            """, (old_token,))
            row = cursor.fetchone()
            if not row:
                return None
            user_id = row['user_id']
            cursor.execute("DELETE FROM refresh_tokens WHERE token = %s", (old_token,))

        new_token = JWTService.generate_refresh_token(user_id)
        return new_token, user_id
