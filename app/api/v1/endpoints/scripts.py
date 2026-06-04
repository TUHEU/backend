# app/api/v1/endpoints/scripts.py

from flask import Blueprint, request
from marshmallow import ValidationError
from app.services.services import ScriptService
from app.schemas.schemas import ScriptCreateSchema, ScriptUpdateSchema
from app.utils.response import ApiResponse
from app.core.security import jwt_required_custom, TokenManager
from app.repositories.repositories import UserRepository

scripts_bp = Blueprint('scripts', __name__, url_prefix='/api/v1/scripts')
_service   = ScriptService()


@scripts_bp.get('/')
@jwt_required_custom
def get_scripts():
    user_id = TokenManager.get_current_user_id()
    scripts = _service.get_all(user_id)
    return ApiResponse.success({'scripts': scripts, 'total': len(scripts)})


@scripts_bp.post('/')
@jwt_required_custom
def create_script():
    try:
        data = ScriptCreateSchema().load(request.get_json() or {})
    except ValidationError as e:
        return ApiResponse.error('Validation failed', 422, e.messages)

    user_id = TokenManager.get_current_user_id()
    result  = _service.create(user_id, data)
    if not result['success']:
        return ApiResponse.error(result['message'], result.get('code', 400))
    return ApiResponse.created({'script': result['script']}, 'Script created')


@scripts_bp.get('/<int:script_id>')
@jwt_required_custom
def get_script(script_id):
    user_id = TokenManager.get_current_user_id()
    result  = _service.get_one(user_id, script_id)
    if not result['success']:
        return ApiResponse.not_found(result['message'])
    return ApiResponse.success({'script': result['script']})


@scripts_bp.put('/<int:script_id>')
@jwt_required_custom
def update_script(script_id):
    try:
        data = ScriptUpdateSchema().load(request.get_json() or {})
    except ValidationError as e:
        return ApiResponse.error('Validation failed', 422, e.messages)

    user_id = TokenManager.get_current_user_id()
    result  = _service.update(user_id, script_id, data)
    if not result['success']:
        return ApiResponse.error(result['message'], result.get('code', 400))
    return ApiResponse.success({'script': result['script']}, 'Script updated')


@scripts_bp.delete('/<int:script_id>')
@jwt_required_custom
def delete_script(script_id):
    user_id = TokenManager.get_current_user_id()
    result  = _service.delete(user_id, script_id)
    if not result['success']:
        return ApiResponse.not_found(result['message'])
    return ApiResponse.success(message='Script deleted')


@scripts_bp.post('/<int:script_id>/apexify')
@jwt_required_custom
def apexify(script_id):
    user_id = TokenManager.get_current_user_id()
    result  = _service.apexify(user_id, script_id)
    if not result['success']:
        return ApiResponse.error(result['message'], result.get('code', 400))
    return ApiResponse.success({'script': result['script']}, 'Script apexified')


@scripts_bp.post('/<int:script_id>/qa')
@jwt_required_custom
def generate_qa(script_id):
    user_id = TokenManager.get_current_user_id()
    result  = _service.generate_qa(user_id, script_id)
    if not result['success']:
        return ApiResponse.error(result['message'], result.get('code', 400))
    return ApiResponse.success({'qa_list': result['qa_list']}, 'Q&A generated')
