from flask import Blueprint, request
from app.services.services import AuthService
from app.utils.response import ok, created, err, unauth
from app.core.security import jwt_required, current_user_id
from app.models.models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')
_svc    = AuthService()

@auth_bp.post('/register')
def register():
    d = request.get_json() or {}
    if not all([d.get('username'), d.get('email'), d.get('password')]):
        return err('username, email and password required', 422)
    if len(d['password']) < 6:
        return err('Password min 6 characters', 422)
    r = _svc.register(d['username'], d['email'], d['password'])
    if not r['ok']: return err(r['msg'], r['code'])
    return created({'user': r['user'], 'access_token': r['token']})

@auth_bp.post('/login')
def login():
    d = request.get_json() or {}
    if not d.get('email') or not d.get('password'):
        return err('email and password required', 422)
    r = _svc.login(d['email'], d['password'])
    if not r['ok']: return err(r['msg'], r['code'])
    return ok({'user': r['user'], 'access_token': r['token']})

@auth_bp.get('/me')
@jwt_required
def me():
    user = User.query.get(current_user_id())
    if not user: return err('User not found', 404)
    return ok({'user': user.to_dict()})
