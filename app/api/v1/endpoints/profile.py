from flask import Blueprint, request
from app.services.services import ProfileService
from app.utils.response import ok, err, not_found
from app.core.security import jwt_required, current_user_id

profile_bp = Blueprint('profile', __name__, url_prefix='/api/v1/profile')
_svc = ProfileService()

@profile_bp.get('/')
@jwt_required
def get_profile():
    user = _svc.get(current_user_id())
    if not user: return not_found()
    return ok({'user': user.to_dict()})

@profile_bp.put('/')
@jwt_required
def update_profile():
    user = _svc.update(current_user_id(), request.get_json() or {})
    if not user: return not_found()
    return ok({'user': user.to_dict()}, 'Profile updated')
