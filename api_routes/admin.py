from flask import jsonify, make_response, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from utils.orm.admin import AdminAccount
from utils.api import http_error_400, json_data_required, admin_required
from utils.mailjet import Mailjet


def add_routes(app):
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
                  "sur la plateforme MetaBank Admin." \
                  "Copier / coller le code suivant dans le formulaire pour pouvoir créer un nouveau mot de passe."
        html_content = "<html><head><title>MetaBank</title><body>Reset password token : {0}</body></head>" \
                       "</html>".format(admin.get('otp_token'))
        mailjet = Mailjet()
        email_sent, http_code, message = mailjet.send_basic_mail(
            to={'email': admin.get('email'), 'name': admin.get('firstname')}, subject=subject, txt_message=content,
            html_message=html_content)

        json_data = {
            'status': email_sent,
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
        html_content = "<html><head><title>MetaBank</title><body>Votre mot de passe a été réinitialisé avec succès." \
                       "</body></head></html>"
        mailjet = Mailjet()
        email_sent, email_http_code, email_message = mailjet.send_basic_mail(
            to={'email': admin.get('email'), 'name': admin.get('firstname')}, subject=subject, txt_message=content,
            html_message=html_content)

        json_data = {
            'status': status,
            'message': message
        }
        if not email_sent:
            json_data['error'] = 'Error while sending email confirmation'
        return make_response(jsonify(json_data), http_code)
