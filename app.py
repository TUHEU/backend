# backend/app.py
"""
Talent Bridge — Flask Application Entry Point
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, jsonify
from flask_cors import CORS

from config.settings import Config
from config.database import init_db

# Blueprints
from routes.auth_routes      import auth_bp
from routes.user_routes      import user_bp
from routes.ai_routes        import ai_bp
from routes.jobs_routes      import jobs_bp
from routes.community_routes import community_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    app.config['DEBUG']      = Config.DEBUG
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024   # 10 MB upload limit

    # CORS — allow all origins in dev; restrict in prod
    CORS(app, resources={r'/api/*': {'origins': '*'}},
         supports_credentials=True)

    # Register blueprints
    for bp in (auth_bp, user_bp, ai_bp, jobs_bp, community_bp):
        app.register_blueprint(bp)

    # ── Global error handlers ───────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(_):
        return jsonify({'message': 'Endpoint not found'}), 404

    @app.errorhandler(405)
    def method_not_allowed(_):
        return jsonify({'message': 'Method not allowed'}), 405

    @app.errorhandler(413)
    def file_too_large(_):
        return jsonify({'message': 'File too large. Max size is 10 MB.'}), 413

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error(f'Internal error: {e}')
        return jsonify({'message': 'An internal server error occurred.'}), 500

    # ── Health check ────────────────────────────────────────────────────────
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok', 'app': 'Talent Bridge API'}), 200

    # ── API root ────────────────────────────────────────────────────────────
    @app.route('/api')
    def api_root():
        return jsonify({
            'app':     'Talent Bridge API',
            'version': '1.0.0',
            'endpoints': [
                '/api/auth/register', '/api/auth/login', '/api/auth/verify-email',
                '/api/auth/resend-otp', '/api/auth/forgot-password',
                '/api/auth/reset-password', '/api/auth/refresh', '/api/auth/logout',
                '/api/user/profile',
                '/api/ai/chat', '/api/ai/history',
                '/api/jobs', '/api/jobs/saved', '/api/jobs/applied',
                '/api/community/posts',
            ],
        }), 200

    return app


if __name__ == '__main__':
    Config.validate()

    print('[DB] Initialising database tables...')
    try:
        init_db()
    except Exception as e:
        print(f'[DB] Warning: {e}')

    app = create_app()
    print('[API] Talent Bridge backend starting on http://0.0.0.0:5003')
    app.run(host='0.0.0.0', port=5003, debug=Config.DEBUG, threaded=True)
