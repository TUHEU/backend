# app/core/security.py
# Pattern: Facade — wraps bcrypt + JWT into clean methods

import bcrypt
import secrets
from datetime import datetime, timedelta
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    get_jwt_identity, verify_jwt_in_request,
)
from functools import wraps
from flask import jsonify


class PasswordHasher:
    """Encapsulates bcrypt hashing — Single Responsibility."""

    ROUNDS = 12

    @staticmethod
    def hash(plain: str) -> str:
        return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(PasswordHasher.ROUNDS)).decode()

    @staticmethod
    def verify(plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode(), hashed.encode())


class TokenManager:
    """Encapsulates JWT and refresh token generation."""

    @staticmethod
    def create_access(user_id: int, extra_claims: dict = None) -> str:
        return create_access_token(
            identity=str(user_id),
            additional_claims=extra_claims or {},
        )

    @staticmethod
    def create_refresh() -> tuple[str, datetime, str]:
        """Returns (raw_token, expires_at, token_type)."""
        raw = secrets.token_urlsafe(64)
        expires_at = datetime.utcnow() + timedelta(days=30)
        return raw, expires_at, 'refresh'

    @staticmethod
    def get_current_user_id() -> int:
        return int(get_jwt_identity())


def jwt_required_custom(fn):
    """Custom decorator that returns clean JSON error instead of default."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            return fn(*args, **kwargs)
        except Exception as e:
            return jsonify({'success': False, 'message': 'Invalid or expired token'}), 401
    return wrapper
