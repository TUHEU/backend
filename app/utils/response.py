# app/utils/response.py
# Pattern: Factory — standardised API response builder

from flask import jsonify
from typing import Any, Optional


class ApiResponse:
    """
    Factory class for consistent JSON responses across all endpoints.
    Every endpoint returns the same envelope structure.
    """

    @staticmethod
    def success(data: Any = None, message: str = 'OK', status: int = 200):
        body = {'success': True, 'message': message}
        if data is not None:
            body['data'] = data
        return jsonify(body), status

    @staticmethod
    def created(data: Any = None, message: str = 'Created'):
        return ApiResponse.success(data, message, 201)

    @staticmethod
    def error(message: str, status: int = 400, errors: Optional[dict] = None):
        body = {'success': False, 'message': message}
        if errors:
            body['errors'] = errors
        return jsonify(body), status

    @staticmethod
    def not_found(message: str = 'Resource not found'):
        return ApiResponse.error(message, 404)

    @staticmethod
    def unauthorized(message: str = 'Unauthorized'):
        return ApiResponse.error(message, 401)

    @staticmethod
    def forbidden(message: str = 'Forbidden'):
        return ApiResponse.error(message, 403)

    @staticmethod
    def server_error(message: str = 'Internal server error'):
        return ApiResponse.error(message, 500)

    @staticmethod
    def conflict(message: str = 'Conflict'):
        return ApiResponse.error(message, 409)
