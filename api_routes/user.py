from flask import jsonify, make_response, request
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity, get_jwt
from os import environ as env

from utils.orm.user import UserAccount
from utils.orm.filter import Filter
from utils.api import http_error_400, http_error_401, json_data_required, admin_required
from utils.email import Email
from utils.redis_db import Redis


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
