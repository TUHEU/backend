# app/api/v1/endpoints/profile.py

from flask import Blueprint, request
from app.utils.response import ApiResponse
from app.core.security import jwt_required_custom, TokenManager
from app.repositories.repositories import UserRepository
from app.core.security import PasswordHasher

profile_bp = Blueprint('profile', __name__, url_prefix='/api/v1/profile')
_user_repo = UserRepository()


@profile_bp.get('/')
@jwt_required_custom
def get_profile():
    user_id = TokenManager.get_current_user_id()
    user    = _user_repo.find_by_id(user_id)
    if not user:
        return ApiResponse.not_found('User not found')
    return ApiResponse.success({'user': user.to_dict()})


@profile_bp.put('/')
@jwt_required_custom
def update_profile():
    user_id = TokenManager.get_current_user_id()
    user    = _user_repo.find_by_id(user_id)
    if not user:
        return ApiResponse.not_found('User not found')

    body = request.get_json() or {}

    if 'full_name' in body and body['full_name'].strip():
        user.full_name = body['full_name'].strip()

    if 'password' in body:
        if len(body['password']) < 6:
            return ApiResponse.error('Password must be at least 6 characters', 400)
        user.password_hash = PasswordHasher.hash(body['password'])

    _user_repo.save(user)
    return ApiResponse.success({'user': user.to_dict()}, 'Profile updated')
