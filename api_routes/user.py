from flask import jsonify, make_response, request
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity, get_jwt
from os import environ as env
from datetime import datetime, timedelta

from utils.orm.user import UserAccount, Beneficiary, TokenClaim
from utils.api import http_error_400, http_error_401, json_data_required, user_required
from utils.email import Email
from utils.redis_db import Redis
from utils.magic_link import MagicLink
from utils.security import generate_hash
from utils.polygon import Polygon
from utils.orm.blockchain import TokenOperation


def add_routes(app):
    @app.route('/api/v1/user/is_registered', methods=['POST'])
    @json_data_required
    def is_registered():
        """
        Check if a user is already registered
        :return:
        """
        mandatory_keys = ['email_address']
        for mandatory_key in mandatory_keys:
            if mandatory_key not in request.json:
                return http_error_400(message='Bad request, {0} is missing'.format(mandatory_key))
        email_address = request.json.get('email_address')
        user_account = UserAccount()
        if user_account.is_existing(email_address=email_address) is True:
            json_data = {
                'status': True,
                'message': "success_already_exist"
            }
        else:
            json_data = {
                'status': False,
                'message': "success_not_exist"
            }
        return make_response(jsonify(json_data), 200)

    @app.route('/api/v1/user/register', methods=['POST'])
    @json_data_required
    def register_user():
        """
        Register a new user
        :return:
        """
        mandatory_keys = ['firstname', 'lastname', 'email_address', 'did_token']
        for mandatory_key in mandatory_keys:
            if mandatory_key not in request.json:
                return http_error_400(message='Bad request, {0} is missing'.format(mandatory_key))
        firstname = request.json.get('firstname')
        lastname = request.json.get('lastname')
        email_address = request.json.get('email_address').lower()
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
            status, http_code, message, already_exist = user_account.register(
                email_address=email_address, magiclink_issuer=user_data.get('issuer'),
                public_address=user_data.get('public_address'), firstname=firstname, lastname=lastname)
        else:
            email_address_hash, email_salt = generate_hash(data_to_hash=email_address, salt=env['APP_DB_HASH_SALT'])
            user_account.load({'user_uuid': user_uuid, 'email_hash': email_address_hash, 'deactivated': 0})
            if user_account.get('user_uuid') is None:
                return http_error_401()
            status, http_code, message = user_account.update_account(public_address=user_data.get('public_address'),
                                                                     magiclink_issuer=user_data.get('issuer'),
                                                                     firstname=firstname, lastname=lastname)
        if status is True and user_account.get('public_address') is not None:
            polygon = Polygon()
            status_tx, tx_hash = polygon.send_matic(receiver_address=user_account.get('public_address'),
                                                    nb_token=int(float(env['POLYGON_MATIC_NEW_USER']) * 1000000000))
            token_operation = TokenOperation()
            status_op, http_code_op, message_op = token_operation.add_operation(
                receiver_uuid=user_account.get('user_uuid'), sender_address=env['POLYGON_PUBLIC_KEY'],
                receiver_address=user_account.get('public_address'), token=token_operation.MATIC,
                nb_token=float(env['POLYGON_MATIC_NEW_USER']), tx_hash=tx_hash)
            if status_op is False:
                app.logger.error("Failed to store token operation, tx hash : {0}".format(tx_hash))

        json_data = {
            'status': status,
            'message': message
        }
        return make_response(jsonify(json_data), http_code)

    @app.route('/api/v1/user/decline', methods=['POST'])
    @json_data_required
    def user_decline():
        """
        Decline/remove a user account
        :return:
        """
        mandatory_keys = ['user_uuid']
        for mandatory_key in mandatory_keys:
            if mandatory_key not in request.json:
                return http_error_400(message='Bad request, {0} is missing'.format(mandatory_key))
        user_uuid = request.json.get('user_uuid')

        user_account = UserAccount()
        status, http_code, message = user_account.decline(user_uuid=user_uuid)
        if status is True:
            token_claim = TokenClaim()
            token_claim.deactivate(user_uuid=user_uuid)
            subject = "MetaBank"
            content = "Nous avons bien pris en compte votre demande de ne pas créer votre compte MetaBank " \
                      "et de ne pas profiter des avantages offerts.\n\nL'équipe MetaBank"
            email = Email(app)
            email.send_async(subject=subject, body=content, recipients=[user_account.get('email')])

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

        magic_link = MagicLink()
        status, http_code, message, user_data = magic_link.get_user_info(did_token=did_token)
        if status is False:
            json_data = {
                'status': status,
                'message': message
            }
            return make_response(jsonify(json_data), http_code)

        user_account = UserAccount()
        status, http_code, message = user_account.login(magiclink_issuer=user_data.get('issuer'))
        if status is False and user_account.get('user_uuid') is None:
            status, http_code, message, already_exist = user_account.register(
                email_address=user_data.get('email'), magiclink_issuer=user_data.get('issuer'),
                public_address=user_data.get('public_address'))
            if status is False:
                json_data = {
                    'status': status,
                    'message': message
                }
                return make_response(jsonify(json_data), http_code)

        selfie, selfie_ext = user_account.get_selfie()
        current_date = datetime.utcnow()
        refresh_expiration = current_date + timedelta(seconds=int(env['JWT_REFRESH_TOKEN_EXPIRES']))
        jwt_identity = {'user_uuid': user_account.get('user_uuid'),
                        'created_at': current_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")}
        jwt_token = create_access_token(identity=jwt_identity)
        refresh_token = create_refresh_token(identity=jwt_identity)
        json_data = {
            'status': status,
            'message': message,
            'jwt_token': jwt_token,
            'refresh_token': refresh_token,
            'refresh_expiration': refresh_expiration.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            'account': {
                'email_address': user_account.get('email'),
                'user_uuid': user_account.get('user_uuid'),
                'firstname': user_account.get('firstname'),
                'lastname': user_account.get('lastname'),
                'birthdate': user_account.get('birthdate'),
                'created_date': user_account.get('created_date'),
                'updated_date': user_account.get('updated_date'),
                'public_address': user_account.get('public_address'),
                'selfie': selfie,
                'selfie_ext': selfie_ext
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

    @app.route('/api/v1/user/account', methods=['POST'])
    @json_data_required
    @jwt_required()
    @user_required
    def update_user_account():
        """
        Update personal account information of the user
        :return:
        """
        firstname = request.json.get('firstname')
        lastname = request.json.get('lastname')
        birthdate = request.json.get('birthdate')
        selfie = request.json.get('selfie')
        selfie_ext = request.json.get('selfie_ext')

        user_uuid = get_jwt_identity().get('user_uuid')

        user_account = UserAccount()
        user_account.load({'user_uuid': user_uuid})
        status, http_code, message = user_account.update_account(firstname=firstname, lastname=lastname,
                                                                 birthdate=birthdate, selfie=selfie,
                                                                 selfie_extension=selfie_ext)
        json_data = {
            'status': status,
            'message': message
        }
        return make_response(jsonify(json_data), http_code)

    @app.route('/api/v1/user/account', methods=['GET'])
    @app.route('/api/v1/user/account/<user_uuid>', methods=['GET'])
    @jwt_required()
    @user_required
    def get_user_account(user_uuid=None):
        """
        Return personal account information or public profile of the given user uuid
        :return:
        """
        user_account = UserAccount()
        if user_uuid is None:
            user_uuid = get_jwt_identity().get('user_uuid')
            user_account.load({'user_uuid': user_uuid})
            selfie, selfie_ext = user_account.get_selfie()
            balances = {}
            if user_account.get('public_address') is not None:
                polygon = Polygon()
                balances = polygon.get_balance(address=user_account.get('public_address'))
            token_claim = TokenClaim()
            to_claim, total_to_claim = token_claim.get_token_claims(user_uuid=user_uuid, claimed=False)
            already_claimed, total_claimed = token_claim.get_token_claims(user_uuid=user_uuid, claimed=True)
            json_data = {
                'status': True,
                'message': 'success_account',
                'account': {
                    'email_address': user_account.get('email'),
                    'user_uuid': user_account.get('user_uuid'),
                    'firstname': user_account.get('firstname'),
                    'lastname': user_account.get('lastname'),
                    'birthdate': user_account.get('birthdate'),
                    'created_date': user_account.get('created_date'),
                    'updated_date': user_account.get('updated_date'),
                    'public_address': user_account.get('public_address'),
                    'selfie': selfie,
                    'selfie_ext': selfie_ext
                },
                'wallet': balances,
                'token_claims': {
                    'to_claim': to_claim,
                    'total_to_claim': total_to_claim,
                    'already_claimed': already_claimed,
                    'total_claimed': total_claimed
                }

            }
        else:
            user_account.load({'user_uuid': user_uuid})
            selfie, selfie_ext = user_account.get_selfie()
            json_data = {
                'status': True,
                'message': 'success_account',
                'account': {
                    'user_uuid': user_account.get('user_uuid'),
                    'firstname': user_account.get('firstname'),
                    'lastname': user_account.get('lastname'),
                    'email_address': user_account.get('email'),
                    'public_address': user_account.get('public_address'),
                    'selfie': selfie,
                    'selfie_ext': selfie_ext
                }
            }
        return make_response(jsonify(json_data), 200)

    @app.route('/api/v1/user/operations', methods=['GET'])
    @jwt_required()
    @user_required
    def get_user_operations():
        """
        Return user CAA operations
        :return:
        """
        in_page_key = request.args.get('in_page_key')
        out_page_key = request.args.get('out_page_key')

        user_uuid = get_jwt_identity().get('user_uuid')
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
        return make_response(jsonify(json_data), 200)

    @app.route('/api/v1/user/search', methods=['POST'])
    @json_data_required
    @jwt_required()
    @user_required
    def search_user():
        """
        Search a user by email or public address
        :return:
        """
        mandatory_keys = ['email_address']
        for mandatory_key in mandatory_keys:
            if mandatory_key not in request.json:
                return http_error_400(message='Bad request, {0} is missing'.format(mandatory_key))
        email_address = request.json.get('email_address')

        user_account = UserAccount()
        status, http_code, message = user_account.search_user(email_address=email_address)
        if status is False:
            json_data = {
                'status': status,
                'message': message,
                'user': None
            }
        else:
            selfie, selfie_ext = user_account.get_selfie()
            json_data = {
                'status': status,
                'message': message,
                'user': {
                    'user_uuid': user_account.get('user_uuid'),
                    'email_address': user_account.get('email'),
                    'firstname': user_account.get('firstname'),
                    'lastname': user_account.get('lastname'),
                    'public_address': user_account.get('public_address'),
                    'selfie': selfie,
                    'selfie_ext': selfie_ext
                }
            }
        return make_response(jsonify(json_data), http_code)

    @app.route('/api/v1/user/beneficiary', methods=['POST'])
    @json_data_required
    @jwt_required()
    @user_required
    def add_beneficiary():
        """
        Add a beneficiary to the user account
        :return:
        """
        beneficiary_user_uuid = request.json.get('user_uuid')
        email_address = request.json.get('email_address')
        public_address = request.json.get('public_address')
        token = request.json.get('2fa_token')

        user_uuid = get_jwt_identity().get('user_uuid')
        user_account = UserAccount()
        user_account.load({'user_uuid': user_uuid})

        if token is None:
            status, http_code, message = user_account.set_otp_token()
            if status is True:
                delay = int(env['APP_TOKEN_DELAY']) // 60
                subject = "MetaBank - Ajout d'un bénéficiaire"
                content = "Renseigner le code suivant pour valider l'ajout du bénéficiaire (valide {0} minutes) :\n" \
                          "{1}".format(delay, user_account.get('otp_token'))
                email = Email(app)
                email.send_async(subject=subject, body=content, recipients=[user_account.get('email')])
        else:
            status, http_code, message = user_account.check_otp_token(token=token)
            if status is False:
                json_data = {
                    'status': status,
                    'message': message
                }
                return make_response(jsonify(json_data), http_code)
            beneficiary = Beneficiary()
            if beneficiary_user_uuid is not None:
                user_account = UserAccount()
                user_account.load({'user_uuid': beneficiary_user_uuid})
                if user_account.get('user_uuid') is None:
                    return http_error_400()
                status, http_code, message = beneficiary.add_new(user_uuid=user_uuid,
                                                                 beneficiary_user_uuid=beneficiary_user_uuid)
            else:
                status, http_code, message = beneficiary.add_new(user_uuid=user_uuid, email=email_address,
                                                                 public_address=public_address)
        json_data = {
            'status': status,
            'message': message
        }
        return make_response(jsonify(json_data), http_code)

    @app.route('/api/v1/user/beneficiary', methods=['GET'])
    @jwt_required()
    @user_required
    def get_beneficiaries():
        """
        Get the beneficiaries of the connected user
        :return:
        """
        user_uuid = get_jwt_identity().get('user_uuid')

        beneficiary = Beneficiary()
        status, http_code, message, beneficiaries = beneficiary.get_beneficiaries(user_uuid=user_uuid)
        json_data = {
            'status': status,
            'message': message,
            'beneficiaries': beneficiaries
        }
        return make_response(jsonify(json_data), http_code)

    @app.route('/api/v1/user/beneficiary/remove', methods=['POST'])
    @json_data_required
    @jwt_required()
    @user_required
    def remove_beneficiary():
        """
        Remove a beneficiary from user list
        :return:
        """
        mandatory_keys = ['beneficiary_uuid']
        for mandatory_key in mandatory_keys:
            if mandatory_key not in request.json:
                return http_error_400(message='Bad request, {0} is missing'.format(mandatory_key))
        beneficiary_uuid = request.json.get('beneficiary_uuid')

        user_uuid = get_jwt_identity().get('user_uuid')

        beneficiary = Beneficiary()
        status, http_code, message = beneficiary.remove(user_uuid=user_uuid, beneficiary_uuid=beneficiary_uuid)
        json_data = {
            'status': status,
            'message': message
        }
        return make_response(jsonify(json_data), http_code)

    @app.route('/api/v1/user/claim', methods=['POST'])
    @json_data_required
    @jwt_required()
    @user_required
    def claim_caa():
        """
        Claim tokens
        :return:
        """
        mandatory_keys = ['claim_uuid']
        for mandatory_key in mandatory_keys:
            if mandatory_key not in request.json:
                return http_error_400(message='Bad request, {0} is missing'.format(mandatory_key))
        claim_list = request.json.get('claim_uuid')
        if not isinstance(claim_list, list):
            return http_error_400()

        user_uuid = get_jwt_identity().get('user_uuid')
        user_account = UserAccount()
        user_account.load({'user_uuid': user_uuid})
        token_claim = TokenClaim()
        status, http_code, message, transactions = token_claim.claim(user_uuid=user_uuid,
                                                                     user_address=user_account.get('public_address'),
                                                                     claim_list=claim_list)
        json_data = {
            'status': status,
            'message': message,
            'transactions': transactions
        }
        return make_response(jsonify(json_data), http_code)
