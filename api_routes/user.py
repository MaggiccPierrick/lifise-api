from flask import jsonify, make_response, request
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity, get_jwt
from os import environ as env
from datetime import datetime

from utils.orm.user import UserAccount
from utils.orm.filter import Filter
from utils.api import http_error_400, http_error_401, json_data_required, admin_required
from utils.email import Email
from utils.redis_db import Redis
from utils.magic_link import MagicLink


def add_routes(app):
    @app.route('/api/v1/user/register', methods=['POST'])
    @json_data_required
    def register_user():
        """
        Register a new user
        :return:
        """
        mandatory_keys = ['firstname', 'lastname', 'email_address']
        for mandatory_key in mandatory_keys:
            if mandatory_key not in request.json:
                return http_error_400(message='Bad request, {0} is missing'.format(mandatory_key))
        firstname = request.json.get('firstname')
        lastname = request.json.get('lastname')
        email_address = request.json.get('email_address').lower()

        user_account = UserAccount()
        status, http_code, message = user_account.register(firstname=firstname, lastname=lastname,
                                                           email_address=email_address)
        if status is True:
            delay = int(env['APP_TOKEN_DELAY']) // 60
            activation_link = "{0}/account/activate?uuid={1}&token={2}".format(env['APP_FRONT_URL'],
                                                                               user_account.get('user_uuid'),
                                                                               user_account.get('otp_token'))
            subject = "MetaBank Account Confirmation"
            content = "Vous venez de créer un compte sur MetaBank.\n" \
                      "Merci de cliquer sur le lien suivant pour activer votre compte (valide {0} minutes) :\n" \
                      "{1}".format(delay, activation_link)
            email = Email(app)
            email.send_async(subject=subject, body=content, recipients=[user_account.get('email')])

        json_data = {
            'status': status,
            'message': message
        }
        return make_response(jsonify(json_data), http_code)

    @app.route('/api/v1/user/validate', methods=['POST'])
    @json_data_required
    def validate_user():
        """
        Activate user account
        :return:
        """
        mandatory_keys = ['user_uuid', 'token']
        for mandatory_key in mandatory_keys:
            if mandatory_key not in request.json:
                return http_error_400(message='Bad request, {0} is missing'.format(mandatory_key))
        user_uuid = request.json.get('user_uuid')
        token = request.json.get('token')

        user_account = UserAccount()
        user_account.load({'user_uuid': user_uuid})
        status, http_code, message = user_account.check_otp_token(token=token)
        json_data = {
            'status': status,
            'message': message
        }
        return make_response(jsonify(json_data), http_code)

    @app.route('/api/v1/user/login', methods=['POST'])
    @json_data_required
    def login_user():
        """
        Login the user with Magic Link, or create him if not already exists
        :return:
        """
        mandatory_keys = ['did_token']
        for mandatory_key in mandatory_keys:
            if mandatory_key not in request.json:
                return http_error_400(message='Bad request, {0} is missing'.format(mandatory_key))
        did_token = request.json.get('did_token')
        user_uuid = request.json.get('user_uuid')

        magic_link = MagicLink()
        status, http_code, message, user_data = magic_link.get_user_info(did_token=did_token)
        if status is False:
            json_data = {
                'status': status,
                'message': message
            }
            return make_response(jsonify(json_data), http_code)

        user_account = UserAccount()
        if user_uuid is None:
            status, http_code, message = user_account.login(magiclink_issuer=user_data.get('issuer'))
            if status is False and user_account.get('user_uuid') is None:
                status, http_code, message = user_account.register(email_address=user_data.get('email'),
                                                                   magiclink_issuer=user_data.get('issuer'))
                if status is False:
                    json_data = {
                        'status': status,
                        'message': message
                    }
                    return make_response(jsonify(json_data), http_code)
        else:
            status, http_code, message = user_account.login(user_uuid=user_uuid)
            if status is False:
                json_data = {
                    'status': status,
                    'message': message
                }
                return make_response(jsonify(json_data), http_code)
            if user_account.get('issuer') is not None and user_account.get('issuer') != user_data.get('issuer'):
                return http_error_401()

            user_account.update_account(public_address=user_data.get('public_address'),
                                        magiclink_issuer=user_data.get('issuer'))

        jwt_identity = {'user_uuid': user_account.get('user_uuid'),
                        'created_at': datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")}
        jwt_token = create_access_token(identity=jwt_identity)
        refresh_token = create_refresh_token(identity=jwt_identity)
        json_data = {
            'status': status,
            'message': message,
            'jwt_token': jwt_token,
            'refresh_token': refresh_token,
            'account': {
                'email_address': user_account.get('email'),
                'user_uuid': user_account.get('user_uuid'),
                'firstname': user_account.get('firstname'),
                'lastname': user_account.get('lastname'),
                'created_date': user_account.get('created_date'),
                'updated_date': user_account.get('updated_date')
            }
        }
        return make_response(jsonify(json_data), http_code)

    @app.route('/api/v1/login/refresh', methods=['GET'])
    @jwt_required(refresh=True)
    def refresh_login():
        """
        Refresh the jwt token (admin and user)
        :return:
        """
        identity = get_jwt_identity()
        jwt_token = create_access_token(identity=identity)
        json_data = {
            'status': True,
            'message': 'success_refresh',
            'jwt_token': jwt_token
        }
        return make_response(jsonify(json_data), 200)

    @app.route('/api/v1/logout', methods=['GET'])
    @jwt_required(refresh=True)
    def logout():
        """
        Logout : works for user and admin
        :return:
        """
        jti = get_jwt()["jti"]
        user_uuid = get_jwt_identity().get('user_uuid')
        if user_uuid is not None:
            user_account = UserAccount()
            user_account.load({'user_uuid': user_uuid})
            magic_link = MagicLink()
            status, http_code, message = magic_link.logout(issuer=user_account.get('magiclink_issuer'))
            if status is False:
                json_data = {
                    'status': False,
                    'message': 'error_logout'
                }
                return make_response(jsonify(json_data), 503)
        try:
            Redis().get_connection().set(jti, "revoked", ex=int(env['JWT_REFRESH_TOKEN_EXPIRES']))
        except (ConnectionRefusedError, ConnectionError) as e:
            app.logger.warning("Connection to Redis failed - error= {0}".format(e))
            json_data = {
                'status': False,
                'message': 'error_logout'
            }
            response = make_response(jsonify(json_data), 503)
            response.headers['Retry-After'] = '10'
            return response
        json_data = {
            'status': True,
            'message': 'success_logout'
        }
        return make_response(jsonify(json_data), 200)
