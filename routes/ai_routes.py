# backend/routes/ai_routes.py
from flask import Blueprint, request, jsonify, g, Response, stream_with_context
from middleware.auth_middleware import require_auth, require_verified
from services.ai_service import ai_service
from config.database import db_cursor
import json

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')

MAX_HISTORY = 20  # last N messages kept for context


def _get_history(user_id):
    with db_cursor() as (_, cursor):
        cursor.execute(
            """SELECT role, content FROM ai_conversations
               WHERE user_id = %s ORDER BY created_at DESC LIMIT %s""",
            (user_id, MAX_HISTORY)
        )
        rows = cursor.fetchall()
    return [{'role': r['role'], 'content': r['content']} for r in reversed(rows)]


def _save_message(user_id, role, content):
    with db_cursor(commit=True) as (_, cursor):
        cursor.execute(
            'INSERT INTO ai_conversations (user_id, role, content) VALUES (%s, %s, %s)',
            (user_id, role, content)
        )


@ai_bp.route('/chat', methods=['POST'])
@require_auth
@require_verified
def chat():
    data    = request.get_json(force=True) or {}
    message = (data.get('message') or '').strip()
    stream  = bool(data.get('stream', False))

    if not message:
        return jsonify({'message': 'Message is required'}), 400

    history  = _get_history(g.user_id)
    messages = history + [{'role': 'user', 'content': message}]

    _save_message(g.user_id, 'user', message)

    if stream:
        def generate():
            full_response = []
            try:
                for chunk in ai_service.chat(messages, stream=True):
                    full_response.append(chunk)
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                complete = ''.join(full_response)
                _save_message(g.user_id, 'assistant', complete)
                yield f"data: {json.dumps({'done': True})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
        )
    else:
        try:
            response_text = ai_service.chat(messages, stream=False)
            _save_message(g.user_id, 'assistant', response_text)
            return jsonify({'response': response_text}), 200
        except Exception as e:
            return jsonify({'message': f'AI service error: {str(e)}'}), 503


@ai_bp.route('/history', methods=['GET'])
@require_auth
def get_history():
    history = _get_history(g.user_id)
    return jsonify({'messages': history}), 200


@ai_bp.route('/history', methods=['DELETE'])
@require_auth
def clear_history():
    with db_cursor(commit=True) as (_, cursor):
        cursor.execute('DELETE FROM ai_conversations WHERE user_id = %s', (g.user_id,))
    return jsonify({'message': 'Conversation history cleared.'}), 200
