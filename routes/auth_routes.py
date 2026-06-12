# backend/routes/auth_routes.py
from flask import Blueprint, request, jsonify
import re
from models.user_model import User
from services.jwt_service import JWTService
from services.otp_service import OTPService
from services.email_service import email_service
from services.cloudinary_service import cloudinary_service

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

def _token_pair(user):
    return {
        'access_token':  JWTService.generate_access_token(user.id, user.email),
        'refresh_token': JWTService.generate_refresh_token(user.id),
        'user':          user.to_dict(),
    }

def _bad(msg, code=400):
    return jsonify({'message': msg}), code


@auth_bp.route('/register', methods=['POST'])
def register():
    if request.content_type and 'multipart' in request.content_type:
        data = request.form
        image_file = request.files.get('profile_image')
    else:
        data = request.get_json(force=True) or {}
        image_file = None

    full_name = (data.get('full_name') or '').strip()
    email     = (data.get('email') or '').strip().lower()
    phone     = (data.get('phone') or '').strip() or None
    password  = data.get('password') or ''
    dob       = data.get('date_of_birth') or None

    if not full_name:
        return _bad('Full name is required')
    if len(full_name) < 3:
        return _bad('Full name must be at least 3 characters')
    if not EMAIL_RE.match(email):
        return _bad('Invalid email address')
    if len(password) < 8:
        return _bad('Password must be at least 8 characters')
    if not any(c.isupper() for c in password):
        return _bad('Password must contain at least one uppercase letter')
    if not any(c.isdigit() for c in password):
        return _bad('Password must contain at least one number')

    if User.find_by_email(email):
        return _bad('An account with this email already exists', 409)

    user = User.create(full_name=full_name, email=email, password=password,
                       phone=phone, date_of_birth=dob)

    if image_file:
        url = cloudinary_service.upload_profile_image(image_file.stream, user.id)
        if url:
            user.update_profile(profile_image_url=url)

    otp = OTPService.generate()
    OTPService.save(email, otp, 'email_verification')
    email_service.send_verification_email(email, full_name, otp)

    return jsonify({
        'message': 'Account created. Check your email for the verification code.',
        'user': user.to_dict(),
    }), 201


@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    data  = request.get_json(force=True) or {}
    email = (data.get('email') or '').strip().lower()
    otp   = (data.get('otp') or '').strip()

    if not email or not otp:
        return _bad('Email and OTP are required')

    user = User.find_by_email(email)
    if not user:
        return _bad('User not found', 404)
    if user.is_email_verified:
        return jsonify({'message': 'Email already verified'}), 200

    if not OTPService.verify(email, otp, 'email_verification'):
        return _bad('Invalid or expired verification code', 422)

    user.verify_email()
    email_service.send_welcome_email(email, user.full_name)

    return jsonify({'message': 'Email verified successfully.', **_token_pair(user)}), 200


@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    data  = request.get_json(force=True) or {}
    email = (data.get('email') or '').strip().lower()

    user = User.find_by_email(email)
    if not user:
        return _bad('User not found', 404)
    if user.is_email_verified:
        return jsonify({'message': 'Email already verified'}), 200

    otp = OTPService.generate()
    OTPService.save(email, otp, 'email_verification')
    email_service.send_verification_email(email, user.full_name, otp)
    return jsonify({'message': 'Verification code resent.'}), 200


@auth_bp.route('/login', methods=['POST'])
def login():
    data     = request.get_json(force=True) or {}
    email    = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or not password:
        return _bad('Email and password are required')

    user = User.find_by_email(email)
    if not user or not user.check_password(password):
        return _bad('Invalid email or password', 401)

    if not user.is_email_verified:
        return jsonify({
            'message': 'Please verify your email before logging in.',
            'email_unverified': True,
            'email': email,
        }), 403

    return jsonify({'message': 'Login successful.', **_token_pair(user)}), 200


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data  = request.get_json(force=True) or {}
    email = (data.get('email') or '').strip().lower()

    if not EMAIL_RE.match(email):
        return _bad('Invalid email address')

    user = User.find_by_email(email)
    if user:
        otp = OTPService.generate()
        OTPService.save(email, otp, 'password_reset')
        email_service.send_password_reset_email(email, user.full_name, otp)

    return jsonify({'message': 'If this email exists, a reset code has been sent.'}), 200


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data     = request.get_json(force=True) or {}
    email    = (data.get('email') or '').strip().lower()
    otp      = (data.get('otp') or '').strip()
    new_pass = data.get('new_password') or ''

    if not email or not otp or not new_pass:
        return _bad('Email, OTP, and new password are required')
    if len(new_pass) < 8:
        return _bad('Password must be at least 8 characters')

    if not OTPService.verify(email, otp, 'password_reset'):
        return _bad('Invalid or expired reset code', 422)

    user = User.find_by_email(email)
    if not user:
        return _bad('User not found', 404)

    user.set_password(new_pass)
    return jsonify({'message': 'Password reset successfully. You can now log in.'}), 200


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    data  = request.get_json(force=True) or {}
    token = data.get('refresh_token') or ''

    result = JWTService.rotate_refresh_token(token)
    if not result:
        return _bad('Invalid or expired refresh token', 401)

    new_refresh, user_id = result
    user = User.find_by_id(user_id)
    if not user:
        return _bad('User not found', 404)

    return jsonify({
        'access_token':  JWTService.generate_access_token(user.id, user.email),
        'refresh_token': new_refresh,
        'user':          user.to_dict(),
    }), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    data  = request.get_json(force=True) or {}
    token = data.get('refresh_token') or ''
    if token:
        JWTService.revoke_refresh_token(token)
    return jsonify({'message': 'Logged out successfully.'}), 200
