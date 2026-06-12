# backend/middleware/auth_middleware.py
from functools import wraps
from flask import request, jsonify, g
import jwt
from services.jwt_service import JWTService
from config.database import db_cursor


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid Authorization header'}), 401
        token = auth_header.split(' ', 1)[1].strip()
        try:
            payload = JWTService.decode_access_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired. Please log in again.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        g.user_id    = payload['sub']
        g.user_email = payload['email']
        return f(*args, **kwargs)
    return decorated


def require_verified(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        with db_cursor() as (_, cursor):
            cursor.execute(
                'SELECT is_email_verified FROM users WHERE id = %s', (g.user_id,)
            )
            row = cursor.fetchone()
        if not row or not row['is_email_verified']:
            return jsonify({'error': 'Email address not verified'}), 403
        return f(*args, **kwargs)
    return decorated
