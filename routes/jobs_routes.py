# backend/routes/jobs_routes.py
from flask import Blueprint, request, jsonify, g
from middleware.auth_middleware import require_auth
from config.database import db_cursor

jobs_bp = Blueprint('jobs', __name__, url_prefix='/api/jobs')


@jobs_bp.route('', methods=['GET'])
@require_auth
def list_jobs():
    page     = max(1, int(request.args.get('page', 1)))
    per_page = min(50, int(request.args.get('per_page', 20)))
    job_type = request.args.get('type')
    search   = request.args.get('q', '').strip()
    offset   = (page - 1) * per_page

    where_clauses = ['is_active = 1']
    params        = []

    if job_type:
        where_clauses.append('job_type = %s')
        params.append(job_type)
    if search:
        where_clauses.append('(title LIKE %s OR company LIKE %s OR location LIKE %s)')
        like = f'%{search}%'
        params.extend([like, like, like])

    where_sql = ' AND '.join(where_clauses)

    with db_cursor() as (_, cursor):
        cursor.execute(f'SELECT COUNT(*) AS total FROM job_listings WHERE {where_sql}', params)
        total = cursor.fetchone()['total']

        cursor.execute(
            f'SELECT * FROM job_listings WHERE {where_sql} '
            f'ORDER BY created_at DESC LIMIT %s OFFSET %s',
            params + [per_page, offset]
        )
        jobs = cursor.fetchall()

    return jsonify({
        'jobs':     jobs,
        'total':    total,
        'page':     page,
        'per_page': per_page,
        'pages':    -(-total // per_page),
    }), 200


@jobs_bp.route('/<int:job_id>', methods=['GET'])
@require_auth
def get_job(job_id):
    with db_cursor() as (_, cursor):
        cursor.execute('SELECT * FROM job_listings WHERE id = %s AND is_active = 1', (job_id,))
        job = cursor.fetchone()
    if not job:
        return jsonify({'message': 'Job not found'}), 404
    return jsonify({'job': job}), 200


@jobs_bp.route('/<int:job_id>/apply', methods=['POST'])
@require_auth
def apply_job(job_id):
    with db_cursor() as (_, cursor):
        cursor.execute('SELECT id FROM job_listings WHERE id = %s AND is_active = 1', (job_id,))
        if not cursor.fetchone():
            return jsonify({'message': 'Job not found'}), 404

    try:
        with db_cursor(commit=True) as (_, cursor):
            cursor.execute(
                'INSERT INTO job_applications (user_id, job_id) VALUES (%s, %s)',
                (g.user_id, job_id)
            )
        return jsonify({'message': 'Application submitted successfully.'}), 201
    except Exception:
        return jsonify({'message': 'You have already applied to this job.'}), 409


@jobs_bp.route('/applied', methods=['GET'])
@require_auth
def my_applications():
    with db_cursor() as (_, cursor):
        cursor.execute(
            """SELECT ja.id, ja.status, ja.applied_at,
                      jl.title, jl.company, jl.location, jl.job_type, jl.salary_min, jl.salary_max
               FROM job_applications ja
               JOIN job_listings jl ON jl.id = ja.job_id
               WHERE ja.user_id = %s
               ORDER BY ja.applied_at DESC""",
            (g.user_id,)
        )
        apps = cursor.fetchall()
    return jsonify({'applications': apps}), 200


@jobs_bp.route('/<int:job_id>/save', methods=['POST'])
@require_auth
def save_job(job_id):
    try:
        with db_cursor(commit=True) as (_, cursor):
            cursor.execute(
                'INSERT INTO saved_jobs (user_id, job_id) VALUES (%s, %s)',
                (g.user_id, job_id)
            )
        return jsonify({'message': 'Job saved.'}), 201
    except Exception:
        return jsonify({'message': 'Job already saved.'}), 409


@jobs_bp.route('/<int:job_id>/save', methods=['DELETE'])
@require_auth
def unsave_job(job_id):
    with db_cursor(commit=True) as (_, cursor):
        cursor.execute(
            'DELETE FROM saved_jobs WHERE user_id = %s AND job_id = %s',
            (g.user_id, job_id)
        )
    return jsonify({'message': 'Job removed from saved.'}), 200


@jobs_bp.route('/saved', methods=['GET'])
@require_auth
def saved_jobs():
    with db_cursor() as (_, cursor):
        cursor.execute(
            """SELECT jl.*, sj.saved_at
               FROM saved_jobs sj
               JOIN job_listings jl ON jl.id = sj.job_id
               WHERE sj.user_id = %s
               ORDER BY sj.saved_at DESC""",
            (g.user_id,)
        )
        jobs = cursor.fetchall()
    return jsonify({'saved_jobs': jobs}), 200
