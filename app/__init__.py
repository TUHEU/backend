import os, logging
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from app.core.config import Config
from app.core.database import db, migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    JWTManager(app)
    CORS(app, resources={r'/api/*': {'origins': Config.ALLOWED_ORIGINS}},
         supports_credentials=True)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Blueprints
    from app.api.v1.endpoints.auth       import auth_bp
    from app.api.v1.endpoints.recordings import recordings_bp
    from app.api.v1.endpoints.profile    import profile_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(recordings_bp)
    app.register_blueprint(profile_bp)

    @app.get('/health')
    def health():
        return jsonify({'status': 'ok', 'service': 'Apex Speech API v1'})

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({'success': False, 'message': 'Not found'}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'success': False, 'message': str(e)}), 500

    logging.basicConfig(
        level=logging.DEBUG if Config.DEBUG else logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

    return app
