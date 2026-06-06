import bcrypt
from functools import wraps
from flask import jsonify
from flask_jwt_extended import (
    create_access_token, get_jwt_identity, verify_jwt_in_request)

class PasswordHasher:
    @staticmethod
    def hash(plain: str) -> str:
        return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(12)).decode()
    @staticmethod
    def verify(plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode(), hashed.encode())

def make_token(user_id: int) -> str:
    return create_access_token(identity=str(user_id))

def current_user_id() -> int:
    return int(get_jwt_identity())

def jwt_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            return fn(*args, **kwargs)
        except Exception:
            return jsonify({'success': False,
                            'message': 'Invalid or expired token'}), 401
    return wrapper
