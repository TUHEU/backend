# app/__init__.py
# Pattern: Application Factory — creates Flask app with all extensions registered

import os
import logging
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from app.core.config import get_config
from app.core.database import db, migrate


def create_app(config_class=None) -> Flask:
    """
    Application Factory Pattern.
    Creates and configures the Flask application.
    """
    app = Flask(__name__)

    # ── Load Config ──────────────────────────────────────
    cfg = config_class or get_config()
    app.config.from_object(cfg)

    # ── Extensions ───────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    JWTManager(app)
    CORS(app, resources={r"/api/*": {"origins": cfg.ALLOWED_ORIGINS}})

    # ── Upload folder ────────────────────────────────────
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads/audio'), exist_ok=True)

    # ── Register Blueprints ──────────────────────────────
    from app.api.v1.endpoints.auth     import auth_bp
    from app.api.v1.endpoints.scripts  import scripts_bp
    from app.api.v1.endpoints.sessions import sessions_bp
    from app.api.v1.endpoints.profile  import profile_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(scripts_bp)
    app.register_blueprint(sessions_bp)
    app.register_blueprint(profile_bp)

    # ── Global error handlers ────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'success': False, 'message': 'Endpoint not found'}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({'success': False, 'message': 'Method not allowed'}), 405

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

    # ── Health check ─────────────────────────────────────
    @app.get('/health')
    def health():
        return jsonify({'status': 'ok', 'service': 'Apex Speech API', 'version': '1.0.0'})

    # ── Logging ──────────────────────────────────────────
    logging.basicConfig(
        level=logging.DEBUG if app.config.get('DEBUG') else logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    )

    return app
