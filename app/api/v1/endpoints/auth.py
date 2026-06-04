# app/api/v1/endpoints/auth.py

from flask import Blueprint, request
from marshmallow import ValidationError
from app.services.services import AuthService
from app.schemas.schemas import RegisterSchema, LoginSchema
from app.utils.response import ApiResponse
from app.core.security import jwt_required_custom, TokenManager

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')
_service = AuthService()


@auth_bp.post('/register')
def register():
    try:
        data = RegisterSchema().load(request.get_json() or {})
    except ValidationError as e:
        return ApiResponse.error('Validation failed', 422, e.messages)

    result = _service.register(data['full_name'], data['email'], data['password'])
    if not result['success']:
        return ApiResponse.error(result['message'], result.get('code', 400))

    return ApiResponse.created({
        'user':          result['user'],
        'access_token':  result['access_token'],
        'refresh_token': result['refresh_token'],
    }, 'Account created')


@auth_bp.post('/login')
def login():
    try:
        data = LoginSchema().load(request.get_json() or {})
    except ValidationError as e:
        return ApiResponse.error('Validation failed', 422, e.messages)

    result = _service.login(data['email'], data['password'])
    if not result['success']:
        return ApiResponse.error(result['message'], result.get('code', 401))

    return ApiResponse.success({
        'user':          result['user'],
        'access_token':  result['access_token'],
        'refresh_token': result['refresh_token'],
    }, 'Login successful')


@auth_bp.post('/refresh')
def refresh():
    body = request.get_json() or {}
    token = body.get('refresh_token')
    if not token:
        return ApiResponse.error('refresh_token required', 400)
    result = _service.refresh(token)
    if not result['success']:
        return ApiResponse.unauthorized(result['message'])
    return ApiResponse.success({'access_token': result['access_token']})


@auth_bp.post('/logout')
@jwt_required_custom
def logout():
    user_id = TokenManager.get_current_user_id()
    result  = _service.logout(user_id)
    return ApiResponse.success(message=result['message'])
