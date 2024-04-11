from flask import jsonify, make_response, request
from flask_jwt_extended import get_jwt_identity
from functools import wraps

from utils.orm.admin import AdminAccount
from utils.orm.user import UserAccount
from utils.kyc import Synaps


def http_error_400(message="error_bad_request"):
    """
    Standard response for api request issue
    """
    return make_response(jsonify({'status': False, 'message': message}), 400)


def http_error_401(message="error_unauthorized"):
    """
    Standard response for unauthorized api request
    """
    return make_response(jsonify({'status': False, 'message': message}), 401)


def http_error_403(message="error_forbidden"):
    """
    Standard response for forbidden access
    """
    return make_response(jsonify({'status': False, 'message': message}), 403)


def http_error_500(message="error_internal_error"):
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
        return make_response(jsonify(status=False, message="no_json_found"), 400)
    return decorated_function


def admin_required(func):
    """
    Decorator around endpoints that require user to be admin to access the resource.
    :param func: The function wrapped by this decorator.
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        admin_uuid = get_jwt_identity().get('admin_uuid')
        if get_jwt_identity().get('is_admin') is True:
            admin = AdminAccount()
            if admin.is_admin(user_uuid=admin_uuid):
                return func(*args, **kwargs)
        return http_error_401()
    return decorated_function


def user_required(kyc=False):
    """
    Decorator around endpoints that require requester to be a registered user to access the resource.
    :param kyc: set True if KYC is mandatory.
    """
    def decorator(func):
        """
        :param func: The function wrapped by this decorator.
        """
        @wraps(func)
        def decorated_function(*args, **kwargs):
            user_uuid = get_jwt_identity().get('user_uuid')
            if user_uuid is not None:
                user_account = UserAccount()
                user_account.load({'user_uuid': user_uuid, 'deactivated': 0})
                if user_account.get('user_uuid') is not None:
                    if kyc is True:
                        synaps = Synaps()
                        if user_account.get('kyc_status') != synaps.APPROVED:
                            return http_error_403(message="error_kyc")
                    return func(*args, **kwargs)
            return http_error_401()
        return decorated_function
    return decorator
