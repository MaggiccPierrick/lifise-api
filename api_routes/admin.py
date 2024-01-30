from flask import jsonify, make_response, request
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity
from os import environ as env
from datetime import datetime

from utils.orm.admin import AdminAccount
from utils.orm.user import UserAccount, TokenClaim
from utils.orm.filter import Filter, OperatorType
from utils.api import http_error_400, http_error_401, json_data_required, admin_required
from utils.email import Email
from utils.security import generate_hash
from utils.polygon import Polygon


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

            jwt_identity = {'admin_uuid': admin.get('admin_uuid'), 'is_admin': True,
                            'created_at': datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")}
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

    @app.route('/api/v1/admin/account', methods=['POST'])
    @json_data_required
    @jwt_required()
    @admin_required
    def update_admin_account():
        """
        Update personal account information
        :return:
        """
        email_address = request.json.get('email_address')
        firstname = request.json.get('firstname')
        lastname = request.json.get('lastname')
        old_password = request.json.get('old_password')
        new_password = request.json.get('new_password')

        admin_uuid = get_jwt_identity().get('admin_uuid')

        admin = AdminAccount()
        admin.load({'admin_uuid': admin_uuid})
        status, http_code, message = admin.update_account(email_address=email_address, firstname=firstname,
                                                          lastname=lastname, old_password=old_password,
                                                          new_password=new_password)
        if status is True:
            subject = "MetaBank Admin - update account"
            content = "Votre compte admin vient d'être mis à jour."
            email = Email(app)
            email.send_async(subject=subject, body=content, recipients=[admin.get('email')])
        json_data = {
            'status': status,
            'message': message
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
        if status is True:
            subject = "MetaBank Admin"
            content = "Un compte administrateur vient d'être créé avec votre adresse email.\n" \
                      "Rendez vous sur la page suivante pour créer votre mot de passe :\n" \
                      "{0}/admin/signin".format(env['APP_FRONT_URL'])
            email = Email(app)
            email.send_async(subject=subject, body=content, recipients=[admin.get('email')])
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

    @app.route('/api/v1/admin', methods=['GET'])
    @jwt_required()
    @admin_required
    def get_admin_accounts():
        """
        Get all admin accounts
        :return:
        """
        deactivated = 0
        if request.args.get('deactivated') == 'true':
            deactivated = 1

        admin = AdminAccount()
        filter_obj = Filter()
        filter_obj.add('deactivated', str(deactivated))
        admin_accounts = admin.list(filter_object=filter_obj)
        admin_list = []
        for admin_account in admin_accounts:
            email_validated = False
            if admin_account.get('email_validated') == 1:
                email_validated = True
            account_deactivated = True
            if admin_account.get('deactivated') == 0:
                account_deactivated = False

            admin_list.append({
                'email_address': admin_account.get('email'),
                'admin_uuid': admin_account.get('admin_uuid'),
                'firstname': admin_account.get('firstname'),
                'lastname': admin_account.get('lastname'),
                'email_validated': email_validated,
                'last_login_date': admin_account.get('last_login'),
                'created_date': admin_account.get('created_date'),
                'updated_date': admin_account.get('updated_date'),
                'deactivated': account_deactivated,
                'deactivated_date': admin_account.get('deactivated_date')
            })

        json_data = {
            'status': True,
            'message': 'success_admin_accounts',
            'admin_accounts': admin_list
        }
        return make_response(jsonify(json_data), 200)

    @app.route('/api/v1/admin/deactivate', methods=['POST'])
    @json_data_required
    @jwt_required()
    @admin_required
    def deactivate_admin():
        """
        Deactivate an admin account
        :return:
        """
        mandatory_keys = ['admin_uuid']
        for mandatory_key in mandatory_keys:
            if mandatory_key not in request.json:
                return http_error_400(message='Bad request, {0} is missing'.format(mandatory_key))
        admin_uuid = request.json.get('admin_uuid')
        connected_admin_uuid = get_jwt_identity().get('admin_uuid')
        if connected_admin_uuid == admin_uuid:
            return http_error_401()

        admin = AdminAccount()
        status, http_code, message = admin.deactivate_admin(admin_uuid=admin_uuid)
        json_data = {
            'status': status,
            'message': message
        }
        return make_response(jsonify(json_data), http_code)

    @app.route('/api/v1/admin/reactivate', methods=['POST'])
    @json_data_required
    @jwt_required()
    @admin_required
    def reactivate_admin():
        """
        Reactivate an admin account
        :return:
        """
        mandatory_keys = ['admin_uuid']
        for mandatory_key in mandatory_keys:
            if mandatory_key not in request.json:
                return http_error_400(message='Bad request, {0} is missing'.format(mandatory_key))
        admin_uuid = request.json.get('admin_uuid')
        connected_admin_uuid = get_jwt_identity().get('admin_uuid')
        if connected_admin_uuid == admin_uuid:
            return http_error_401()

        admin = AdminAccount()
        status, http_code, message = admin.reactivate_admin(admin_uuid=admin_uuid)
        json_data = {
            'status': status,
            'message': message
        }
        return make_response(jsonify(json_data), http_code)

    @app.route('/api/v1/admin/user/invite', methods=['POST'])
    @json_data_required
    @jwt_required()
    @admin_required
    def invite_users():
        """
        Invite a list of users by email
        :return:
        """
        mandatory_keys = ['emails_list', 'claimable_tokens']
        for mandatory_key in mandatory_keys:
            if mandatory_key not in request.json:
                return http_error_400(message='Bad request, {0} is missing'.format(mandatory_key))
        emails_list = request.json.get('emails_list')
        claimable_tokens = float(request.json.get('claimable_tokens'))

        if not isinstance(emails_list, list) or len(emails_list) == 0:
            return http_error_400()

        admin_uuid = get_jwt_identity().get('admin_uuid')
        unique_emails = list(set(emails_list))

        not_created = []
        existed = []
        user_account = UserAccount()
        email = Email(app)
        email_subject = "Créez votre compte MetaBank"
        invitation_link = "{0}/signup?user_uuid=".format(env['APP_FRONT_URL'])
        decline_link = "{0}/decline?user_uuid=".format(env['APP_FRONT_URL'])

        for email_address in unique_emails:
            status, http_code, message, already_exist = user_account.register(email_address=email_address)
            if status is False and already_exist is False:
                not_created.append(email_address)
                continue
            if status is False and already_exist is True:
                existed.append(email_address)
                email_address_hash, email_salt = generate_hash(data_to_hash=email_address, salt=env['APP_DB_HASH_SALT'])
                user_account.load({'email_hash': email_address_hash})
            else:
                if claimable_tokens > 0:
                    content = "MetaBank vous invite à créer votre compte dès maintenant " \
                              "et vous offre {0} CAA euros.\n\n" \
                              "Cliquez sur le lien suivant pour créer votre compte et obtenir vos CAA :\n" \
                              "{1}{2}\n\n" \
                              "Si vous ne souhaitez pas créer votre compte MetaBank, " \
                              "cliquez sur le lien suivant pour refuser et ne plus recevoir nos messages :\n" \
                              "{3}{4}\n\nL'équipe MetaBank".format(claimable_tokens, invitation_link,
                                                                   user_account.get('user_uuid'), decline_link,
                                                                   user_account.get('user_uuid'))
                else:
                    content = "MetaBank vous invite à créer votre compte dès maintenant.\n\n" \
                              "Cliquez sur le lien suivant pour créer votre compte :\n" \
                              "{0}{1}\n\n" \
                              "Si vous ne souhaitez pas créer votre compte MetaBank, " \
                              "cliquez sur le lien suivant pour refuser et ne plus recevoir nos messages :\n" \
                              "{2}{3}\n\nL'équipe MetaBank".format(invitation_link, user_account.get('user_uuid'),
                                                                   decline_link, user_account.get('user_uuid'))
                email.send_async(subject=email_subject, body=content, recipients=[user_account.get('email')])
            if claimable_tokens > 0:
                token_claim = TokenClaim()
                token_claim.create(creator_uuid=admin_uuid, user_uuid=user_account.get('user_uuid'),
                                   nb_token=claimable_tokens)

        if len(existed) > 0 and claimable_tokens > 0:
            subject = "MetaBank vous offre des euros"
            content = "MetaBank vous offre {0} CAA euros.\n" \
                      "Connectez-vous à votre compte pour les percevoir.".format(claimable_tokens)
            email.send_async(subject=subject, body=content, recipients=[env['EMAIL_ADDRESS']], bcc=existed)

        json_data = {
            'status': True,
            'message': 'success_user_accounts',
            'accounts_not_created': not_created
        }
        return make_response(jsonify(json_data), 200)

    @app.route('/api/v1/admin/users', methods=['GET'])
    @jwt_required()
    @admin_required
    def get_users_accounts():
        """
        Get all users accounts
        :return:
        """
        deactivated = 0
        if request.args.get('deactivated') == 'true':
            deactivated = 1

        pending = False
        if request.args.get('pending') == 'true':
            pending = True

        user_account = UserAccount()
        filter_user = Filter()
        filter_user.add('deactivated', str(deactivated))
        if deactivated == 0:
            if pending is True:
                filter_user.add('public_address', operator=OperatorType.IN)
            else:
                filter_user.add('public_address', operator=OperatorType.INN)
        user_accounts = user_account.list(filter_object=filter_user, order='lastname', asc='ASC')

        token_claim = TokenClaim()
        polygon = Polygon()
        users_list = []
        for current_user in user_accounts:
            email_validated = False
            if current_user.get('email_validated') == 1:
                email_validated = True
            account_deactivated = True
            if current_user.get('deactivated') == 0:
                account_deactivated = False
            selfie, selfie_ext = user_account.get_selfie(filename=current_user.get('selfie'))
            to_claim, total_to_claim = token_claim.get_token_claims(user_uuid=current_user.get('user_uuid'),
                                                                    claimed=False)
            already_claimed, total_claimed = token_claim.get_token_claims(user_uuid=current_user.get('user_uuid'),
                                                                          claimed=True)
            balances = {}
            if current_user.get('public_address') is not None:
                balances = polygon.get_balance(address=current_user.get('public_address'))
            users_list.append({
                'email_address': current_user.get('email'),
                'user_uuid': current_user.get('user_uuid'),
                'firstname': current_user.get('firstname'),
                'lastname': current_user.get('lastname'),
                'birthdate': current_user.get('birthdate'),
                'email_validated': email_validated,
                'last_login_date': current_user.get('last_login'),
                'created_date': current_user.get('created_date'),
                'updated_date': current_user.get('updated_date'),
                'deactivated': account_deactivated,
                'deactivated_date': current_user.get('deactivated_date'),
                'public_address': current_user.get('public_address'),
                'selfie': selfie,
                'selfie_ext': selfie_ext,
                'token_claims': {
                    'to_claim': to_claim,
                    'total_to_claim': total_to_claim,
                    'already_claimed': already_claimed,
                    'total_claimed': total_claimed
                },
                'wallet': balances,
            })

        json_data = {
            'status': True,
            'message': 'success_user_accounts',
            'user_accounts': users_list
        }
        return make_response(jsonify(json_data), 200)

    @app.route('/api/v1/admin/user/operations/<user_uuid>', methods=['GET'])
    @jwt_required()
    @admin_required
    def admin_get_user_operations(user_uuid):
        """
        Get user onchain CAA operations
        :return:
        """
        in_page_key = request.args.get('in_page_key')
        out_page_key = request.args.get('out_page_key')

        user_account = UserAccount()
        user_account.load({'user_uuid': user_uuid})
        if user_account.get('public_address') is None:
            json_data = {
                'status': False,
                'message': 'error_no_address'
            }
            return make_response(jsonify(json_data), 200)

        polygon = Polygon()
        status, http_code, message, operations, out_page_key, in_page_key = polygon.get_operations(
            address=user_account.get('public_address'), in_page_key=in_page_key, out_page_key=out_page_key)

        json_data = {
            'status': status,
            'message': message,
            'operations': operations,
            'out_page_key': out_page_key,
            'in_page_key': in_page_key
        }
        return make_response(jsonify(json_data), http_code)

    @app.route('/api/v1/admin/user/deactivate', methods=['POST'])
    @json_data_required
    @jwt_required()
    @admin_required
    def deactivate_user():
        """
        Deactivate a user account
        :return:
        """
        mandatory_keys = ['user_uuid']
        for mandatory_key in mandatory_keys:
            if mandatory_key not in request.json:
                return http_error_400(message='Bad request, {0} is missing'.format(mandatory_key))
        user_uuid = request.json.get('user_uuid')

        user_account = UserAccount()
        status, http_code, message = user_account.deactivate_user(user_uuid=user_uuid)
        json_data = {
            'status': status,
            'message': message
        }
        return make_response(jsonify(json_data), http_code)

    @app.route('/api/v1/admin/user/reactivate', methods=['POST'])
    @json_data_required
    @jwt_required()
    @admin_required
    def reactivate_user():
        """
        Reactivate a user account
        :return:
        """
        mandatory_keys = ['user_uuid']
        for mandatory_key in mandatory_keys:
            if mandatory_key not in request.json:
                return http_error_400(message='Bad request, {0} is missing'.format(mandatory_key))
        user_uuid = request.json.get('user_uuid')

        user_account = UserAccount()
        status, http_code, message = user_account.reactivate_user(user_uuid=user_uuid)
        json_data = {
            'status': status,
            'message': message
        }
        return make_response(jsonify(json_data), http_code)

    @app.route('/api/v1/admin/wallet/balance', methods=['GET'])
    @jwt_required()
    @admin_required
    def get_wallet_balance():
        """
        Get platform wallet balances (CAA & MATIC)
        :return:
        """
        polygon = Polygon()
        balances = polygon.get_balance(address=env['POLYGON_PUBLIC_KEY'])
        json_data = {
            'status': True,
            'message': 'success_wallet_balance',
            'balances': balances,
            'address': env['POLYGON_PUBLIC_KEY']
        }
        return make_response(jsonify(json_data), 200)
