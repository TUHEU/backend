# app/api/v1/endpoints/sessions.py

from flask import Blueprint, request
from marshmallow import ValidationError
from app.services.services import SessionService
from app.schemas.schemas import SessionStartSchema, PostureEventSchema, SessionFinishSchema
from app.utils.response import ApiResponse
from app.core.security import jwt_required_custom, TokenManager

sessions_bp = Blueprint('sessions', __name__, url_prefix='/api/v1/sessions')
_service    = SessionService()


@sessions_bp.post('/start')
@jwt_required_custom
def start_session():
    try:
        data = SessionStartSchema().load(request.get_json() or {})
    except ValidationError as e:
        return ApiResponse.error('Validation failed', 422, e.messages)

    user_id = TokenManager.get_current_user_id()
    result  = _service.start(user_id, data.get('script_id'))
    return ApiResponse.created({'session_id': result['session_id']}, 'Session started')


@sessions_bp.post('/<int:session_id>/audio')
@jwt_required_custom
def upload_audio(session_id):
    if 'audio' not in request.files:
        return ApiResponse.error('No audio file provided', 400)

    audio_bytes = request.files['audio'].read()
    result      = _service.process_audio_chunk(session_id, audio_bytes)
    if not result['success']:
        return ApiResponse.error(result['message'], result.get('code', 400))

    return ApiResponse.success({
        'transcription':    result.get('transcription', ''),
        'filler_events':    result.get('filler_events', []),
        'confidence_score': result.get('confidence_score', 0),
        'enthusiasm_score': result.get('enthusiasm_score', 0),
        'authority_score':  result.get('authority_score', 0),
    })


@sessions_bp.post('/<int:session_id>/posture')
@jwt_required_custom
def save_posture(session_id):
    try:
        data = PostureEventSchema().load(request.get_json() or {})
    except ValidationError as e:
        return ApiResponse.error('Validation failed', 422, e.messages)

    result = _service.save_posture_event(
        session_id,
        data['event_type'],
        data['timestamp_seconds'],
        data.get('duration_seconds', 0.0),
    )
    if not result['success']:
        return ApiResponse.error(result['message'], result.get('code', 400))
    return ApiResponse.success(message='Posture event saved')


@sessions_bp.post('/<int:session_id>/finish')
@jwt_required_custom
def finish_session(session_id):
    try:
        data = SessionFinishSchema().load(request.get_json() or {})
    except ValidationError as e:
        return ApiResponse.error('Validation failed', 422, e.messages)

    result = _service.finish(session_id, data['duration_seconds'])
    if not result['success']:
        return ApiResponse.error(result['message'], result.get('code', 400))
    return ApiResponse.success({'session': result['session']}, 'Session completed')


@sessions_bp.get('/')
@jwt_required_custom
def get_sessions():
    user_id = TokenManager.get_current_user_id()
    result  = _service.get_all(user_id)
    return ApiResponse.success({'sessions': result['sessions'], 'total': len(result['sessions'])})


@sessions_bp.get('/<int:session_id>/report')
@jwt_required_custom
def get_report(session_id):
    user_id = TokenManager.get_current_user_id()
    result  = _service.get_report(session_id, user_id)
    if not result['success']:
        return ApiResponse.not_found(result['message'])
    return ApiResponse.success({
        'session':        result['session'],
        'filler_events':  result['filler_events'],
        'posture_events': result['posture_events'],
        'coaching_tips':  result['coaching_tips'],
    })
