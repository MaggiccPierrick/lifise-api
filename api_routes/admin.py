import pyotp

from flask import jsonify, make_response, request
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity
from os import environ as env
from datetime import datetime

from utils.orm.admin import AdminAccount
from utils.orm.user import UserAccount, TokenClaim, UserPurchase
from utils.orm.filter import Filter, OperatorType
from utils.api import http_error_400, http_error_401, http_error_403, json_data_required, admin_required
from utils.email import Sendgrid
from utils.security import generate_hash
from utils.provider import Provider
from utils.orm.blockchain import TokenOperation


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
                subject = "LiFiSe Admin - 2FA login"
                content = "Une nouvelle connexion à votre compte admin sur LiFiSe vient d'être réalisée.<br>" \
                          "Entrez le code d'authentification suivant (expire dans {0} minutes) :".format(delay)
                sendgrid = Sendgrid()
                sendgrid.send_email(to_emails=[admin.get('email')], subject=subject, txt_content=content,
                                    token=admin.get('otp_token'))

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
            subject = "LiFiSe Admin - update account"
            content = "Votre compte admin vient d'être mis à jour."
            sendgrid = Sendgrid()
            sendgrid.send_email(to_emails=[admin.get('email')], subject=subject, txt_content=content)
        json_data = {
            'status': status,
            'message': message
        }
        return make_response(jsonify(json_data), http_code)

    @app.route('/api/v1/admin/totp/generate', methods=['GET'])
    @jwt_required()
    @admin_required
    def generate_otp():
        """
        Generate OTP secret key
        :return:
        """
        admin_uuid = get_jwt_identity().get('admin_uuid')

        otp_base32 = pyotp.random_base32()
        otp_auth_url = pyotp.totp.TOTP(otp_base32).provisioning_uri(name="Admin", issuer_name=env['APP_NAME'])

        admin = AdminAccount()
        admin.load({'admin_uuid': admin_uuid})
        status, http_code, message = admin.update_account(otp_url=otp_auth_url, otp_base32=otp_base32)

        json_data = {
            'status': status,
            'message': "success_totp",
            'base32': otp_base32,
            'otp_auth_url': otp_auth_url
        }
        return make_response(jsonify(json_data), http_code)

    @app.route('/api/v1/admin/totp/activate', methods=['POST'])
    @json_data_required
    @jwt_required()
    @admin_required
    def activate_otp():
        """
        Activate OTP
        :return:
        """
        mandatory_keys = ['totp_token']
        for mandatory_key in mandatory_keys:
            if mandatory_key not in request.json:
                return http_error_400(message='Bad request, {0} is missing'.format(mandatory_key))
        totp_token = request.json.get('totp_token')

        admin_uuid = get_jwt_identity().get('admin_uuid')

        admin = AdminAccount()
        admin.load({'admin_uuid': admin_uuid})
        status, http_code, message = admin.verify_totp(token=totp_token)
        if status is True:
            admin.enable_totp()

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
            subject = "LiFiSe Admin"
            content = "Un compte administrateur vient d'être créé avec votre adresse email.<br>" \
                      "Rendez vous sur la page suivante pour créer votre mot de passe :<br>" \
                      "{0}/admin/signin".format(env['APP_FRONT_URL'])
            sendgrid = Sendgrid()
            sendgrid.send_email(to_emails=[admin.get('email')], subject=subject, txt_content=content)
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

        subject = "LiFiSe Admin - reset password"
        content = "Nous venons de recevoir une demande de réinitialisation de votre mot de passe " \
                  "sur la plateforme LiFiSe Admin.<br>" \
                  "Copiez / collez le code suivant dans le formulaire pour pouvoir créer un nouveau mot de passe."
        sendgrid = Sendgrid()
        email_sent = sendgrid.send_email(to_emails=[admin.get('email')], subject=subject, txt_content=content,
                                         token=admin.get('otp_token'))
        if email_sent is False:
            json_data = {
                'status': False,
                'message': "error_email_not_sent"
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

        subject = "LiFiSe Admin - mot de passe réinitialisé"
        content = "Votre mot de passe a été réinitialisé avec succès."
        sendgrid = Sendgrid()
        email_sent = sendgrid.send_email(to_emails=[admin.get('email')], subject=subject, txt_content=content)
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
            'message': "success_admin_accounts",
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
        sendgrid = Sendgrid()
        email_subject = "Créez votre compte LiFiSe"
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
                    content = "Vous êtes invité à rejoindre LiFiSe et à collecter votre cadeau " \
                              "de {nb_token} EUR LFS en cliquant sur le lien suivant :<br>" \
                              "{invitation_link}{user_uuid}<br>" \
                              "<br>LiFiSe est la première Néo-banque Française web3 grand public. " \
                              "C’est une Fintech Mass Market issue de l’univers crypto.<br>" \
                              "LiFiSe c’est : un exchange, un euro stable coin et " \
                              "un utility Token de Gouvernance.<br>" \
                              "Notre Slogan : « Liberty – Safety – Trust »<br><br>" \
                              "Pour nous rejoindre, vous devez disposer d’une simple adresse email " \
                              "et suivre votre lien d'enregistrement ci-dessus puis vous laisser guider !<br><br>" \
                              "Si vous ne souhaitez pas créer votre compte LiFiSe, " \
                              "cliquez sur le lien suivant pour refuser et ne plus recevoir nos messages :<br>" \
                              "{decline_link}{user_uuid}".format(nb_token=claimable_tokens,
                                                                 invitation_link=invitation_link,
                                                                 user_uuid=user_account.get('user_uuid'),
                                                                 decline_link=decline_link)
                else:
                    content = "Vous êtes invité à rejoindre LiFiSe en cliquant sur le lien suivant :<br>" \
                              "{invitation_link}{user_uuid}<br>" \
                              "<br>LiFiSe est la première Néo-banque Française web3 grand public. " \
                              "C’est une Fintech Mass Market issue de l’univers crypto.<br>" \
                              "LiFiSe c’est : un exchange, un euro stable coin et " \
                              "un utility Token de Gouvernance.<br>" \
                              "Notre Slogan : « Liberty – Safety – Trust »<br><br>" \
                              "Pour nous rejoindre, vous devez disposer d’une simple adresse email " \
                              "et suivre votre lien d'enregistrement ci-dessus puis vous laisser guider !<br><br>" \
                              "Si vous ne souhaitez pas créer votre compte LiFiSe, " \
                              "cliquez sur le lien suivant pour refuser et ne plus recevoir nos messages :<br>" \
                              "{decline_link}{user_uuid}".format(invitation_link=invitation_link,
                                                                 user_uuid=user_account.get('user_uuid'),
                                                                 decline_link=decline_link)
                sendgrid.send_email(to_emails=[user_account.get('email')], subject=email_subject, txt_content=content)
            if claimable_tokens > 0:
                token_claim = TokenClaim()
                token_claim.create(creator_uuid=admin_uuid, user_uuid=user_account.get('user_uuid'),
                                   nb_token=claimable_tokens)

        if len(existed) > 0 and claimable_tokens > 0:
            subject = "LiFiSe vous offre des euros"
            content = "LiFiSe vous offre {0} EUR LFS.<br>" \
                      "Connectez-vous à votre compte pour les collecter.".format(claimable_tokens)
            sendgrid.send_email(to_emails=existed, subject=subject, txt_content=content)

        json_data = {
            'status': True,
            'message': "success_user_accounts",
            'accounts_not_created': not_created
        }
        return make_response(jsonify(json_data), 200)

    @app.route('/api/v1/admin/users', methods=['GET'])
    @app.route('/api/v1/admin/users/<user_uuid>', methods=['GET'])
    @jwt_required()
    @admin_required
    def get_users_accounts(user_uuid=None):
        """
        Get all users accounts
        :return:
        """
        user_account = UserAccount()
        token_claim = TokenClaim()
        if user_uuid is None:
            deactivated = 0
            if request.args.get('deactivated') == 'true':
                deactivated = 1

            pending = False
            if request.args.get('pending') == 'true':
                pending = True

            filter_user = Filter()
            filter_user.add('deactivated', str(deactivated))
            if deactivated == 0:
                if pending is True:
                    filter_user.add('public_address', operator=OperatorType.IN)
                else:
                    filter_user.add('public_address', operator=OperatorType.INN)
            user_accounts = user_account.list(filter_object=filter_user, order='lastname', asc='ASC')

            users_list = []
            for current_user in user_accounts:
                email_validated = False
                if current_user.get('email_validated') == 1:
                    email_validated = True
                account_deactivated = True
                if current_user.get('deactivated') == 0:
                    account_deactivated = False

                to_claim, total_to_claim = token_claim.get_token_claims(user_uuid=current_user.get('user_uuid'),
                                                                        claimed=False)
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
                    'token_claims': {
                        'to_claim': to_claim,
                        'total_to_claim': total_to_claim
                    },
                    'kyc_status': current_user.get('kyc_status'),
                    'kyc_status_date': current_user.get('kyc_status_date')
                })

            json_data = {
                'status': True,
                'message': "success_user_accounts",
                'user_accounts': users_list
            }
        else:
            user_account.load({'user_uuid': user_uuid})
            email_validated = False
            if user_account.get('email_validated') == 1:
                email_validated = True
            account_deactivated = True
            if user_account.get('deactivated') == 0:
                account_deactivated = False
            selfie, selfie_ext = user_account.get_selfie(filename=user_account.get('selfie'))
            already_claimed, total_claimed = token_claim.get_token_claims(user_uuid=user_account.get('user_uuid'),
                                                                          claimed=True)
            to_claim, total_to_claim = token_claim.get_token_claims(user_uuid=user_account.get('user_uuid'),
                                                                    claimed=False)
            provider = Provider()
            balances = {}
            if user_account.get('public_address') is not None:
                balances = provider.get_balance(address=user_account.get('public_address'))
            user_details = {
                'email_address': user_account.get('email'),
                'user_uuid': user_account.get('user_uuid'),
                'firstname': user_account.get('firstname'),
                'lastname': user_account.get('lastname'),
                'birthdate': user_account.get('birthdate'),
                'email_validated': email_validated,
                'last_login_date': user_account.get('last_login'),
                'created_date': user_account.get('created_date'),
                'updated_date': user_account.get('updated_date'),
                'deactivated': account_deactivated,
                'deactivated_date': user_account.get('deactivated_date'),
                'public_address': user_account.get('public_address'),
                'selfie': selfie,
                'selfie_ext': selfie_ext,
                'token_claims': {
                    'to_claim': to_claim,
                    'total_to_claim': total_to_claim,
                    'already_claimed': already_claimed,
                    'total_claimed': total_claimed
                },
                'wallet': balances,
                'kyc_status': user_account.get('kyc_status'),
                'kyc_status_date': user_account.get('kyc_status_date')
            }
            json_data = {
                'status': True,
                'message': "success_user_accounts",
                'user_details': user_details
            }
        return make_response(jsonify(json_data), 200)

    @app.route('/api/v1/admin/user/operations/<user_uuid>', methods=['GET'])
    @jwt_required()
    @admin_required
    def admin_get_user_operations(user_uuid):
        """
        Get user onchain EUR LFS operations
        :return:
        """
        in_page_key = request.args.get('in_page_key')
        out_page_key = request.args.get('out_page_key')

        user_account = UserAccount()
        user_account.load({'user_uuid': user_uuid})
        if user_account.get('public_address') is None:
            json_data = {
                'status': False,
                'message': "error_no_address"
            }
            return make_response(jsonify(json_data), 200)

        provider = Provider()
        status, http_code, message, operations, out_page_key, in_page_key = provider.get_operations(
            address=user_account.get('public_address'), in_page_key=in_page_key, out_page_key=out_page_key)

        token_claim = TokenClaim()
        filter_claim = Filter()
        filter_claim.add('user_uuid', user_uuid)
        user_claims = token_claim.list(fields=['token_claim_uuid', 'tx_hash'], filter_object=filter_claim)
        tx_hash_claim = {}
        for current_claim in user_claims:
            if current_claim.get('tx_hash') is not None:
                tx_hash_claim[current_claim.get('tx_hash')] = current_claim.get('token_claim_uuid')

        for current_op in operations:
            current_op['claim_uuid'] = tx_hash_claim.get(current_op.get('hash'))

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

    @app.route('/api/v1/admin/user/purchase/order', methods=['GET'])
    @app.route('/api/v1/admin/user/purchase/order/<user_uuid>', methods=['GET'])
    @jwt_required()
    @admin_required
    def admin_get_user_orders(user_uuid=None):
        """
        Get user orders
        :return:
        """
        pending = None
        if request.args.get('pending') == 'false':
            pending = False
        if request.args.get('pending') == 'true':
            pending = True

        user_purchase = UserPurchase()
        filter_purchase = Filter()
        if user_uuid is not None:
            filter_purchase.add('user_uuid', user_uuid)
        if pending is not None:
            if pending is True:
                filter_purchase.add('amount_received', operator=OperatorType.IN)
            else:
                filter_purchase.add('amount_received', operator=OperatorType.INN)

        purchase_list = user_purchase.list(fields=['user_purchase_uuid', 'user_uuid', 'nb_token', 'total_price_eur',
                                                   'reference', 'amount_received', 'payment_date', 'tx_hash',
                                                   'created_date'],
                                           filter_object=filter_purchase, order='created_date', asc='DESC')
        user_list = []
        user_details = {}
        if len(purchase_list) > 0:
            for current_purchase in purchase_list:
                if current_purchase.get('user_uuid') not in user_list:
                    user_list.append(current_purchase.get('user_uuid'))

            filter_users = Filter()
            filter_users.add('user_uuid', user_list, operator=OperatorType.IIN)
            user_account = UserAccount()
            users_info = user_account.list(fields=['user_uuid', 'firstname', 'lastname', 'email', 'public_address',
                                                   'kyc_status'],
                                           filter_object=filter_users)
            for current_user in users_info:
                user_details[current_user.get('user_uuid')] = {
                    'firstname': current_user.get('firstname'),
                    'lastname': current_user.get('lastname'),
                    'email': current_user.get('email'),
                    'public_address': current_user.get('public_address'),
                    'kyc_status': current_user.get('kyc_status')
                }

        json_data = {
            'status': True,
            'message': "success_purchase",
            'orders': purchase_list,
            'user_info': user_details
        }
        return make_response(jsonify(json_data), 200)

    @app.route('/api/v1/admin/user/purchase/order/confirm', methods=['POST'])
    @json_data_required
    @jwt_required()
    @admin_required
    def order_confirm_payment():
        """
        Confirm order payment received
        :return:
        """
        mandatory_keys = ['user_uuid', 'user_purchase_uuid', 'amount_received']
        for mandatory_key in mandatory_keys:
            if mandatory_key not in request.json:
                return http_error_400(message='Bad request, {0} is missing'.format(mandatory_key))
        user_uuid = request.json.get('user_uuid')
        user_purchase_uuid = request.json.get('user_purchase_uuid')
        amount_received = float(request.json.get('amount_received'))
        if amount_received <= 0:
            return http_error_400()

        user_account = UserAccount()
        user_account.load({'user_uuid': user_uuid})
        if user_account.get('public_address') is None:
            return http_error_400(message="error_public_address")

        user_purchase = UserPurchase()
        user_purchase.load({'user_uuid': user_uuid, 'user_purchase_uuid': user_purchase_uuid})
        if user_purchase.get('amount_received') is not None:
            return http_error_400(message="error_already_confirmed")

        transaction = {
            user_purchase_uuid: {
                'receiver': user_account.get('public_address'),
                'nb_token': amount_received
            }
        }
        provider = Provider()
        status_tx, http_code_tx, message_tx, tx_hash = provider.send_batch_tx(transactions=transaction)
        if status_tx is True:
            status, message, http_code = user_purchase.confirm_payment(amount_received=amount_received,
                                                                       tx_hash=tx_hash.get(user_purchase_uuid))
            if status is False:
                app.logger.error("Error during payment confirmation, tx hash = {0}".format(
                    tx_hash.get(user_purchase_uuid)))

            token_operation = TokenOperation()
            status_op, http_code_op, message_op = token_operation.add_operation(
                receiver_uuid=user_uuid, sender_address=env['ADMIN_WALLET_PUBLIC_KEY'],
                receiver_address=user_account.get('public_address'), token=token_operation.EUROLFS,
                nb_token=amount_received, tx_hash=tx_hash.get(user_purchase_uuid))
            if status_op is False:
                app.logger.error("Failed to store token operation, tx hash : {0}".format(tx_hash))

            sendgrid = Sendgrid()
            subject = "LiFiSe - traitement de votre achat"
            content = "Nous vous remercions pour l’ordre passé sur notre plateforme. Nous vous confirmons " \
                      "la bonne réception de votre paiement et l’envoie des Tokens vers votre compte " \
                      "LiFiSe. Encore une fois, merci pour votre confiance.<br>" \
                      "Détails de votre achat :<br>" \
                      "Référence : {0}<br>" \
                      "Commande : {1} EUR LFS<br>" \
                      "Montant total reçu : {2} EUR<br>" \
                      "Nombre de tokens envoyés : {3}".format(user_purchase.get('reference'),
                                                              user_purchase.get('nb_token'),
                                                              amount_received, amount_received)
            sendgrid.send_email(to_emails=[user_account.get('email')], subject=subject, txt_content=content)

        json_data = {
            'status': status_tx,
            'message': message_tx
        }
        return make_response(jsonify(json_data), http_code_tx)

    @app.route('/api/v1/admin/wallet/balance', methods=['GET'])
    @jwt_required()
    @admin_required
    def get_wallet_balance():
        """
        Get platform wallet balances (EUR LFS & Native token)
        :return:
        """
        provider = Provider()
        balances = provider.get_balance(address=env['ADMIN_WALLET_PUBLIC_KEY'])

        json_data = {
            'status': True,
            'message': "success_wallet_balance",
            'balances': balances,
            'address': env['ADMIN_WALLET_PUBLIC_KEY']
        }
        return make_response(jsonify(json_data), 200)
