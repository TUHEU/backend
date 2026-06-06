import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY               = os.getenv('SECRET_KEY', 'dev-secret-key')
    JWT_SECRET_KEY           = os.getenv('JWT_SECRET_KEY', 'jwt-dev-secret')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 86400))
    OPENAI_API_KEY           = os.getenv('OPENAI_API_KEY', '')
    UPLOAD_FOLDER            = os.getenv('UPLOAD_FOLDER', 'uploads/audio')
    ALLOWED_ORIGINS          = os.getenv('ALLOWED_ORIGINS',
                                 'http://localhost:3000').split(',')

    _pw = quote_plus(os.getenv('DB_PASSWORD', ''))
    _u  = os.getenv('DB_USER', 'root')
    _h  = os.getenv('DB_HOST', 'localhost')
    _p  = os.getenv('DB_PORT', '3306')
    _n  = os.getenv('DB_NAME', 'apexspeech_db')

    SQLALCHEMY_DATABASE_URI        = f'mysql+pymysql://{_u}:{_pw}@{_h}:{_p}/{_n}?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS      = {'pool_recycle': 280, 'pool_pre_ping': True}
    DEBUG                          = os.getenv('FLASK_DEBUG', 'True') == 'True'
