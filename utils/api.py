from flask import jsonify, make_response, request
from functools import wraps


def http_error_400(message="Bad request"):
    """
    Standard response for api request issue
    """
    return make_response(jsonify({'status': False, 'message': message}), 400)


def http_error_401(message="Unauthorized"):
    """
    Standard response for unauthorized api request
    """
    return make_response(jsonify({'status': False, 'message': message}), 401)


def http_error_403(message="Forbidden"):
    """
    Standard response for forbidden access
    """
    return make_response(jsonify({'status': False, 'message': message}), 403)


def http_error_500(message="Internal error"):
    """
    Standard response for api request issue
    """
    return make_response(jsonify({'status': False, 'message': message}), 500)


def json_data_required(func):
    """
    Decorator around endpoints that require user to provide POST data.
    It will reject queries without json_data.
    :param func: The function wrapped by this decorator.
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if request.get_json():
            return func(*args, **kwargs)
        return make_response(jsonify(status=False, message="No JSON found"), 400)
    return decorated_function
