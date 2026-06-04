# app/core/config.py
# Pattern: Config Object Pattern — environment-specific config classes

import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()


def _build_db_uri():
    """
    URL-encode the password so special characters like @, #, $ don't
    break the SQLAlchemy connection string.
    Example: Fahdil@1  →  Fahdil%401
    """
    user     = os.getenv('DB_USER',     'root')
    password = quote_plus(os.getenv('DB_PASSWORD', ''))   # ← encodes @ # $ etc.
    host     = os.getenv('DB_HOST',     'localhost')
    port     = os.getenv('DB_PORT',     '3306')
    name     = os.getenv('DB_NAME',     'apexspeech_db')
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"


class BaseConfig:
    """Base configuration — all shared settings."""
    SECRET_KEY                = os.getenv('SECRET_KEY',       'dev-secret-key')
    JWT_SECRET_KEY            = os.getenv('JWT_SECRET_KEY',   'jwt-dev-secret')
    JWT_ACCESS_TOKEN_EXPIRES  = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES',  3600))
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000))

    DB_HOST     = os.getenv('DB_HOST',     'localhost')
    DB_PORT     = os.getenv('DB_PORT',     '3306')
    DB_NAME     = os.getenv('DB_NAME',     'apexspeech_db')
    DB_USER     = os.getenv('DB_USER',     'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')

    SQLALCHEMY_DATABASE_URI        = _build_db_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
        'pool_size': 10,
        'max_overflow': 20,
    }

    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    HUME_API_KEY   = os.getenv('HUME_API_KEY',   '')

    UPLOAD_FOLDER      = os.getenv('UPLOAD_FOLDER', 'uploads/audio')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 52428800))

    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')

    GPT_APEXIFY_SYSTEM_PROMPT = (
        "You are an elite executive speech coach. Refine the following speech for maximum impact. "
        "Remove all filler words and jargon. Add a powerful hook in the first sentence. "
        "Vary sentence length for rhythm and authority. End with a memorable call to action. "
        "Return ONLY the refined speech text, nothing else."
    )
    GPT_QA_SYSTEM_PROMPT = (
        "You are a tough audience member at a high-stakes presentation. "
        "Generate exactly 5 challenging questions that an audience might ask about the given speech. "
        "For each question also provide a concise suggested talking-point answer. "
        "Return ONLY valid JSON array: "
        '[{"question":"...","suggested_answer":"...","difficulty":"easy|medium|hard"}]'
    )


class DevelopmentConfig(BaseConfig):
    FLASK_ENV = 'development'
    DEBUG     = True


class ProductionConfig(BaseConfig):
    FLASK_ENV = 'production'
    DEBUG     = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        **BaseConfig.SQLALCHEMY_ENGINE_OPTIONS,
        'pool_size': 20,
        'max_overflow': 40,
    }


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config_map = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'testing':     TestingConfig,
}


def get_config():
    env = os.getenv('FLASK_ENV', 'development')
    return config_map.get(env, DevelopmentConfig)