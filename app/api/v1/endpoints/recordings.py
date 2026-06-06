from flask import Blueprint, request
from app.services.services import RecordingService
from app.utils.response import ok, created, err, not_found
from app.core.security import jwt_required, current_user_id

recordings_bp = Blueprint('recordings', __name__,
                           url_prefix='/api/v1/recordings')
_svc = RecordingService()

def _uid():
    """Optional JWT — returns user_id or None."""
    try:
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        verify_jwt_in_request(optional=True)
        v = get_jwt_identity()
        return int(v) if v else None
    except Exception:
        return None

@recordings_bp.get('/')
def list_recordings():
    uid  = _uid()
    recs = _svc.get_all(user_id=uid)
    return ok({'recordings': [r.to_dict() for r in recs],
               'total': len(recs)})

@recordings_bp.post('/')
def create_recording():
    d = request.get_json() or {}
    if not d.get('title'): return err('title is required', 422)
    rec = _svc.create(d, user_id=_uid())
    return created({'recording': rec.to_dict()})

@recordings_bp.get('/<int:rid>')
def get_recording(rid):
    rec = _svc.get_one(rid)
    if not rec: return not_found()
    return ok({'recording': rec.to_dict()})

@recordings_bp.delete('/<int:rid>')
def delete_recording(rid):
    ok_ = _svc.delete(rid, user_id=_uid())
    if not ok_: return not_found('Recording not found or not authorized')
    return ok(msg='Deleted')

@recordings_bp.post('/<int:rid>/feedback')
def get_feedback(rid):
    result = _svc.get_feedback(rid)
    if result is None: return not_found()
    return ok({'score':    result['score'],
               'feedback': result['feedback'],
               'model':    result['model']})

@recordings_bp.get('/stats')
@jwt_required
def get_stats():
    uid = current_user_id()
    return ok({'stats': _svc.get_stats(uid)})
