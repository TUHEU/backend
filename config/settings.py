# backend/config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ── Database ──────────────────────────────────────────────
    DB_HOST     = os.getenv('DB_HOST', 'localhost')
    DB_PORT     = int(os.getenv('DB_PORT', 3306))
    DB_USER     = os.getenv('DB_USER', 'root')
    DB_PASS     = os.getenv('DB_PASS', '')
    DB_NAME     = os.getenv('DB_NAME', 'talent_bridge')

    # ── JWT ───────────────────────────────────────────────────
    JWT_SECRET          = os.getenv('JWT_SECRET', 'change-this-secret')
    JWT_EXPIRY_HOURS    = int(os.getenv('JWT_EXPIRY_HOURS', 24))
    JWT_REFRESH_DAYS    = int(os.getenv('JWT_REFRESH_DAYS', 30))

    # ── Brevo ─────────────────────────────────────────────────
    BREVO_API_KEY       = os.getenv('BREVO_API_KEY')
    BREVO_SENDER_EMAIL  = os.getenv('BREVO_SENDER_EMAIL')
    BREVO_SENDER_NAME   = os.getenv('BREVO_SENDER_NAME', 'Talent Bridge')

    # ── Cloudinary ────────────────────────────────────────────
    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY    = os.getenv('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')

    # ── AI ────────────────────────────────────────────────────
    AI_PROVIDER  = os.getenv('AI_PROVIDER', 'gemini')
    AI_API_KEY   = os.getenv('AI_API_KEY')
    AI_MODEL     = os.getenv('AI_MODEL')

    # ── Flask ─────────────────────────────────────────────────
    DEBUG        = os.getenv('FLASK_ENV') == 'development'
    SECRET_KEY   = os.getenv('JWT_SECRET', 'flask-secret')

    # ── OTP ───────────────────────────────────────────────────
    OTP_EXPIRY_MINUTES = 10
    OTP_LENGTH         = 6

    @classmethod
    def validate(cls):
        required = ['DB_PASS', 'JWT_SECRET', 'BREVO_API_KEY', 'BREVO_SENDER_EMAIL']
        missing = [k for k in required if not getattr(cls, k)]
        if missing:
            print(f"[WARNING] Missing env vars: {missing}")
