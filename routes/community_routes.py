# backend/routes/community_routes.py
from flask import Blueprint, request, jsonify, g
from middleware.auth_middleware import require_auth, require_verified
from config.database import db_cursor

community_bp = Blueprint('community', __name__, url_prefix='/api/community')


@community_bp.route('/posts', methods=['GET'])
@require_auth
def list_posts():
    page     = max(1, int(request.args.get('page', 1)))
    per_page = min(50, int(request.args.get('per_page', 20)))
    offset   = (page - 1) * per_page

    with db_cursor() as (_, cursor):
        cursor.execute('SELECT COUNT(*) AS total FROM community_posts', ())
        total = cursor.fetchone()['total']
        cursor.execute(
            """SELECT cp.id, cp.content, cp.likes, cp.created_at,
                      u.id AS user_id, u.full_name, u.profile_image_url, u.job_title
               FROM community_posts cp
               JOIN users u ON u.id = cp.user_id
               ORDER BY cp.created_at DESC
               LIMIT %s OFFSET %s""",
            (per_page, offset)
        )
        posts = cursor.fetchall()

    return jsonify({
        'posts': posts, 'total': total,
        'page': page, 'per_page': per_page,
    }), 200


@community_bp.route('/posts', methods=['POST'])
@require_auth
@require_verified
def create_post():
    data    = request.get_json(force=True) or {}
    content = (data.get('content') or '').strip()

    if not content:
        return jsonify({'message': 'Post content is required'}), 400
    if len(content) > 2000:
        return jsonify({'message': 'Post is too long (max 2000 characters)'}), 400

    with db_cursor(commit=True) as (_, cursor):
        cursor.execute(
            'INSERT INTO community_posts (user_id, content) VALUES (%s, %s)',
            (g.user_id, content)
        )
        post_id = cursor.lastrowid

    return jsonify({'message': 'Post created.', 'post_id': post_id}), 201


@community_bp.route('/posts/<int:post_id>/like', methods=['POST'])
@require_auth
def like_post(post_id):
    with db_cursor(commit=True) as (_, cursor):
        cursor.execute(
            'UPDATE community_posts SET likes = likes + 1 WHERE id = %s', (post_id,)
        )
        cursor.execute('SELECT likes FROM community_posts WHERE id = %s', (post_id,))
        row = cursor.fetchone()
    if not row:
        return jsonify({'message': 'Post not found'}), 404
    return jsonify({'likes': row['likes']}), 200


@community_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@require_auth
def delete_post(post_id):
    with db_cursor(commit=True) as (_, cursor):
        rows = cursor.execute(
            'DELETE FROM community_posts WHERE id = %s AND user_id = %s',
            (post_id, g.user_id)
        )
    if not rows:
        return jsonify({'message': 'Post not found or not yours'}), 404
    return jsonify({'message': 'Post deleted.'}), 200
