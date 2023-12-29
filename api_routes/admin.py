from flask import jsonify, make_response, request
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity
from os import environ as env

from utils.orm.admin import AdminAccount
from utils.api import http_error_400, json_data_required, admin_required
from utils.email import Email


def add_routes(app):
    @app.route('/api/v1/admin/login', methods=['POST'])
    @json_data_required
    def admin_login():
        """
        Login admin with 2FA token
        :return:
        """
        mandatory_keys = ['login', 'password']
        for mandatory_key in mandatory_keys:
            if mandatory_key not in request.json:
                return http_error_400(message='Bad request, {0} is missing'.format(mandatory_key))
        login = request.json.get('login').lower()
        password = request.json.get('password')
        token = request.json.get('2fa_token')

        admin = AdminAccount()
        if token is None:
            status, http_code, message = admin.login(login=login, password=password)
            if status is True:
                delay = int(env['APP_TOKEN_DELAY']) // 60
                subject = "MetaBank Admin - 2FA login"
                content = "Connexion à votre compte admin sur MetaBank.\n" \
                          "Code d'authentification (valide {0} minutes) : {1}".format(delay, admin.get('otp_token'))
                email = Email(app)
                email.send_async(subject=subject, body=content, recipients=[admin.get('email')])

            json_data = {
                'status': status,
                'message': message
            }

        else:
            status, http_code, message = admin.login(login=login, password=password, token=token)
            if status is False:
                json_data = {
                    'status': status,
                    'message': message
                }
                return make_response(jsonify(json_data), http_code)

            jwt_identity = {'username': admin.get('username'), 'admin_uuid': admin.get('admin_uuid'), 'is_admin': True}
            jwt_token = create_access_token(identity=jwt_identity)
            refresh_token = create_refresh_token(identity=jwt_identity)
            json_data = {
                'status': status,
                'message': message,
                'jwt_token': jwt_token,
                'refresh_token': refresh_token,
                'account': {
                    'email_address': admin.get('email'),
                    'admin_uuid': admin.get('admin_uuid'),
                    'firstname': admin.get('firstname'),
                    'lastname': admin.get('lastname'),
                    'created_date': admin.get('created_date'),
                    'updated_date': admin.get('updated_date')
                }
            }
        return make_response(jsonify(json_data), http_code)

    @app.route('/api/v1/admin/create', methods=['POST'])
    @json_data_required
    @jwt_required()
    @admin_required
    def create_admin_account():
        """
        Create an admin account
        :return:
        """
        mandatory_keys = ['email_address', 'firstname', 'lastname']
        for mandatory_key in mandatory_keys:
            if mandatory_key not in request.json:
                return http_error_400(message='Bad request, {0} is missing'.format(mandatory_key))
        email_address = request.json.get('email_address').lower()
        firstname = request.json.get('firstname')
        lastname = request.json.get('lastname')

        admin_uuid = get_jwt_identity().get('admin_uuid')

        admin = AdminAccount()
        status, http_code, message = admin.create_account(creator_id=admin_uuid, email_address=email_address,
                                                          firstname=firstname, lastname=lastname)
        if status is False:
            return http_error_400(message)

        json_data = {
            'status': status,
            'message': message,
            'user_uuid': admin.get('admin_uuid')
        }
        return make_response(jsonify(json_data), http_code)

    @app.route('/api/v1/admin/password/reset/token', methods=['POST'])
    @json_data_required
    def admin_reset_password_token():
        """
        Create a reset password token for the admin and send it by email
        :return:
        """
        mandatory_keys = ['email_address']
        for mandatory_key in mandatory_keys:
            if mandatory_key not in request.json:
                return http_error_400(message='Bad request, {0} is missing'.format(mandatory_key))
        email_address = request.json.get('email_address').lower()

        admin = AdminAccount()
        status, http_code, message = admin.create_otp_token(email_address=email_address)
        if status is False:
            json_data = {
                'status': status,
                'message': message
            }
            return make_response(jsonify(json_data), http_code)

        subject = "MetaBank Admin - reset password"
        content = "Nous venons de recevoir une demande de réinitialisation de votre mot de passe " \
                  "sur la plateforme MetaBank Admin.\n" \
                  "Copier / coller le code suivant dans le formulaire pour pouvoir créer un nouveau mot de passe.\n" \
                  "{0}".format(admin.get('otp_token'))
        email = Email(app)
        email_sent = email.send_async(subject=subject, body=content, recipients=[admin.get('email')])
        if email_sent is False:
            json_data = {
                'status': False,
                'message': 'Failed to send token by email'
            }
            return make_response(jsonify(json_data), 503)

        json_data = {
            'status': status,
            'message': message
        }
        return make_response(jsonify(json_data), http_code)

    @app.route('/api/v1/admin/password/reset', methods=['POST'])
    @json_data_required
    def admin_reset_password():
        """
        Reset the password of the admin
        :return:
        """
        mandatory_keys = ['email_address', 'password', 'reset_token']
        for mandatory_key in mandatory_keys:
            if mandatory_key not in request.json:
                return http_error_400(message='Bad request, {0} is missing'.format(mandatory_key))
        password = request.json.get('password')
        reset_token = request.json.get('reset_token')
        email_address = request.json.get('email_address')

        admin = AdminAccount()
        status, http_code, message = admin.reset_password(email_address=email_address, new_password=password,
                                                          reset_token=reset_token)
        if status is False:
            json_data = {
                'status': status,
                'message': message
            }
            return make_response(jsonify(json_data), http_code)

        subject = "MetaBank Admin - mot de passe réinitialisé"
        content = "Votre mot de passe a été réinitialisé avec succès."
        email = Email(app)
        email_sent = email.send_async(subject=subject, body=content, recipients=[admin.get('email')])
        json_data = {
            'status': status,
            'message': message
        }
        if not email_sent:
            json_data['error'] = 'Error while sending email confirmation'
        return make_response(jsonify(json_data), http_code)
