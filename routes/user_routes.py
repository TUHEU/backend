# backend/routes/user_routes.py
from flask import Blueprint, request, jsonify, g
from middleware.auth_middleware import require_auth
from models.user_model import User
from services.cloudinary_service import cloudinary_service

user_bp = Blueprint('user', __name__, url_prefix='/api/user')


@user_bp.route('/profile', methods=['GET'])
@require_auth
def get_profile():
    user = User.find_by_id(g.user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    return jsonify({'user': user.to_dict()}), 200


@user_bp.route('/profile', methods=['PUT'])
@require_auth
def update_profile():
    if request.content_type and 'multipart' in request.content_type:
        data = request.form
        image_file = request.files.get('profile_image')
    else:
        data = request.get_json(force=True) or {}
        image_file = None

    user = User.find_by_id(g.user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    updates = {}
    for field in ('full_name', 'phone', 'date_of_birth', 'bio', 'job_title', 'company'):
        val = data.get(field)
        if val is not None:
            updates[field] = val.strip() if isinstance(val, str) else val

    if image_file:
        url = cloudinary_service.upload_profile_image(image_file.stream, user.id)
        if url:
            updates['profile_image_url'] = url

    if updates:
        user.update_profile(**updates)

    return jsonify({'message': 'Profile updated.', 'user': user.to_dict()}), 200


@user_bp.route('/change-password', methods=['POST'])
@require_auth
def change_password():
    data         = request.get_json(force=True) or {}
    old_password = data.get('old_password') or ''
    new_password = data.get('new_password') or ''

    if not old_password or not new_password:
        return jsonify({'message': 'Both old and new passwords are required'}), 400
    if len(new_password) < 8:
        return jsonify({'message': 'New password must be at least 8 characters'}), 400

    user = User.find_by_id(g.user_id)
    if not user or not user.check_password(old_password):
        return jsonify({'message': 'Current password is incorrect'}), 401

    user.set_password(new_password)
    return jsonify({'message': 'Password changed successfully.'}), 200


@user_bp.route('/delete-account', methods=['DELETE'])
@require_auth
def delete_account():
    data     = request.get_json(force=True) or {}
    password = data.get('password') or ''

    user = User.find_by_id(g.user_id)
    if not user or not user.check_password(password):
        return jsonify({'message': 'Incorrect password'}), 401

    from config.database import db_cursor
    with db_cursor(commit=True) as (_, cursor):
        cursor.execute('DELETE FROM users WHERE id = %s', (g.user_id,))

    return jsonify({'message': 'Account deleted successfully.'}), 200
