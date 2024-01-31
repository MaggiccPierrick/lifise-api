import os

from uuid import uuid4
from datetime import datetime, timedelta
from os import environ as env
from random import randrange

from utils.orm.abstract import Abstract
from utils.orm.filter import Filter
from utils.security import generate_hash
from utils.email import check_email_format
from utils.scaleway import ObjectStorage
from utils.polygon import Polygon
from utils.orm.blockchain import TokenOperation


def user_directory(file_type, file_name):
    """
    Build user files path in object storage
    :param file_type:
    :param file_name:
    :return:
    """
    if file_type not in ['selfie']:
        return False
    return "users/{0}/{1}".format(file_type, file_name)


class UserAccount(Abstract):
    """
    UserAccount class extends the base class <abstract> and provides object-like access to the user DB table.
    """
    def __init__(self, data=None, adapter=None):
        Abstract.__init__(self, data, adapter)
        self._table = 'user_account'
        self._columns = ['user_uuid', 'firstname', 'lastname', 'birthdate', 'email', 'email_hash', 'email_validated',
                         'selfie', 'otp_token', 'otp_expiration', 'public_address', 'magiclink_issuer', 'last_login',
                         'creator_id', 'created_date', 'updated_date', 'deactivated', 'deactivated_date']
        self._encrypt_fields = ['email', 'firstname', 'lastname', 'birthdate', 'otp_token', 'public_address']
        self._primary_key = ['user_uuid']
        self._defaults = {
            'created_date': datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            'email_validated': 0,
            'deactivated': 0
        }

    def register(self, email_address: str, creator_id: str = None, firstname: str = None, lastname: str = None,
                 public_address: str = None, magiclink_issuer: str = None):
        """
        Create a new user account
        :param email_address:
        :param creator_id:
        :param firstname:
        :param lastname:
        :param public_address:
        :param magiclink_issuer:
        :return:
        """
        if firstname is not None and (len(firstname) < 2 or len(firstname) > 30):
            return False, 400, "error_firstname", False
        if lastname is not None and (len(lastname) < 2 or len(lastname) > 30):
            return False, 400, "error_lastname", False

        if check_email_format(email_address) is False:
            return False, 400, "error_email", False

        if self.is_existing(email_address=email_address) is True:
            return False, 400, "error_exist", True

        user_uuid = str(uuid4())
        email_address_hash, email_salt = generate_hash(data_to_hash=email_address, salt=env['APP_DB_HASH_SALT'])
        otp_token = '{:06}'.format(randrange(1, 10 ** 6))
        validity_date = datetime.utcnow() + timedelta(seconds=int(env['APP_TOKEN_DELAY']))
        try:
            self.set_data({
                'creator_id': creator_id,
                'user_uuid': user_uuid,
                'email': email_address,
                'email_hash': email_address_hash,
                'firstname': firstname,
                'lastname': lastname,
                'otp_token': otp_token,
                'otp_expiration': validity_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                'public_address': public_address,
                'magiclink_issuer': magiclink_issuer
            })
            self.insert()
        except Exception as e:
            self.log.error("User registration db error = {0}".format(e))
            return False, 500, "error_user_register", False

        return True, 200, "success_user_register", False

    def decline(self, user_uuid):
        """
        Decline the creation of an account and remove user data
        :param user_uuid:
        :return:
        """
        self.load({'user_uuid': user_uuid, 'deactivated': 0})
        if self.get('user_uuid') is None:
            return False, 401, "error_not_exist"
        if self.get('public_address') is not None:
            return False, 401, 'error_account_active'
        status, http_code, message = self.deactivate_user()
        return status, http_code, message

    def login(self, magiclink_issuer: str):
        """
        Login the user with MagicLink issuer
        :param magiclink_issuer:
        :return:
        """
        self.load({'magiclink_issuer': magiclink_issuer})
        if self.get('user_uuid') is None:
            return False, 401, 'error_not_exist'
        if self.get('deactivated') == 1:
            return False, 401, 'error_deactivated'
        self.set('last_login', datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
        self.update()
        return True, 200, 'success_login'

    def set_otp_token(self):
        """

        :return:
        """
        otp_token = '{:06}'.format(randrange(1, 10 ** 6))
        self.set('otp_token', otp_token)
        validity_date = datetime.utcnow() + timedelta(seconds=int(env['APP_TOKEN_DELAY']))
        self.set('otp_expiration', validity_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
        self.update()
        return True, 200, "success_token_set"

    def check_otp_token(self, token: str):
        """
        Check the otp token for the loaded user
        :param token:
        :return:
        """
        if self.get('user_uuid') is not None and self.get('otp_token') == token:
            if self.get('otp_expiration') < str(datetime.utcnow()):
                self.set('otp_token', None)
                self.set('otp_expiration', None)
                self.update()
                return False, 401, "error_expired"
            else:
                self.set('otp_token', None)
                self.set('otp_expiration', None)
                self.set('email_validated', 1)
                self.update()
                return True, 200, "success_validated"
        else:
            return False, 401, "error_token"

    def is_existing(self, email_address: str):
        """
        Verify if the given account parameters already exist in db
        :param email_address:
        :return:
        """
        email_address_hash, email_salt = generate_hash(data_to_hash=email_address, salt=env['APP_DB_HASH_SALT'])
        filter_user = Filter()
        filter_user.add('email_hash', email_address_hash)
        user_accounts = self.list(fields=['user_uuid'], filter_object=filter_user)
        if len(user_accounts) > 0:
            return True
        return False

    def update_account(self, public_address: str = None, magiclink_issuer: str = None, firstname: str = None,
                       lastname: str = None, birthdate: str = None, selfie: str = None, selfie_extension: str = None):
        """
        Update user data
        :param public_address:
        :param magiclink_issuer:
        :param firstname:
        :param lastname:
        :param birthdate:
        :param selfie:
        :param selfie_extension:
        :return:
        """
        updated = False
        if public_address is not None:
            self.set('public_address', public_address)
            updated = True

        if magiclink_issuer is not None:
            self.set('magiclink_issuer', magiclink_issuer)
            updated = True

        if firstname is not None and 2 <= len(firstname) < 30:
            self.set('firstname', firstname)
            updated = True

        if lastname is not None and 2 <= len(lastname) < 30:
            self.set('lastname', lastname)
            updated = True

        if birthdate is not None:
            try:
                datetime.strptime(birthdate, "%Y-%m-%d")
            except ValueError:
                return False, 400, "error_birthdate"
            self.set('birthdate', birthdate)
            updated = True

        if selfie is not None:
            storage = ObjectStorage()
            storage.get_s3_connexion()
            file_extension = 'jpg'
            if selfie_extension is not None:
                file_extension = selfie_extension[:10]
            filename = "{0}.{1}".format(self.get('user_uuid'), file_extension)
            path = user_directory(file_type='selfie', file_name=filename)
            storage_status = storage.store_object(object_content=selfie, object_path=path)
            if storage_status is False:
                self.log.warning("Something went wrong when storing user selfie on Object storage")
                return False, 503, "Failed to store selfie"
            self.set('selfie', filename)
            updated = True

        if updated is True:
            self.set('deactivated', 0)
            self.set('deactivated_date', None)
            self.set('updated_date', datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
            self.update()
            return True, 200, "success_account_updated"
        else:
            return False, 400, "error_account_update"

    def deactivate_user(self, user_uuid: str = None):
        """
        Deactivate a user
        :param user_uuid:
        :return:
        """
        if user_uuid is not None:
            self.load({'user_uuid': user_uuid})
        if self.get('user_uuid') is not None:
            self.set('deactivated', 1)
            self.set('deactivated_date', datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
            self.update()
            return True, 200, "success_user_deactivated"
        return False, 400, "error_not_exist"

    def reactivate_user(self, user_uuid: str):
        """
        Reactivate a user
        :param user_uuid:
        :return:
        """
        self.load({'user_uuid': user_uuid})
        if self.get('user_uuid') is not None:
            self.set('deactivated', 0)
            self.set('deactivated_date', None)
            self.update()
            return True, 200, "success_user_reactivated"
        return False, 400, "error_not_exist"

    def get_selfie(self, filename=None):
        """
        Return selfie image data
        :param filename:
        :return:
        """
        if filename is not None:
            file_name, file_extension = os.path.splitext(filename)
        elif self.get('selfie') is not None:
            filename = self.get('selfie')
            file_name, file_extension = os.path.splitext(filename)
        else:
            return None, None

        if file_extension is not None:
            file_extension = file_extension[1:]
        path = user_directory(file_type='selfie', file_name=filename)
        storage = ObjectStorage()
        storage.get_s3_connexion()
        selfie = storage.get_object(object_path=path)
        if selfie is not False:
            return selfie, file_extension
        return None, None

    def search_user(self, email_address=None, public_address=None):
        """
        Search a user by email or public address
        :param email_address:
        :param public_address:
        :return:
        """
        if email_address is not None:
            if check_email_format(email_address) is False:
                return False, 400, "error_email"
            email_address_hash, email_salt = generate_hash(data_to_hash=email_address, salt=env['APP_DB_HASH_SALT'])
            self.load({'email_hash': email_address_hash, 'deactivated': 0})
        elif public_address is not None:
            self.load({'public_address': public_address, 'deactivated': 0})
        else:
            return False, 400, "error_bad_request"

        if self.get('user_uuid') is None:
            return False, 200, "success_no_user"

        return True, 200, "success_user_found"


class Beneficiary(Abstract):
    """
    Beneficiary class extends the base class <abstract> and provides object-like access to the beneficiary DB table.
    """
    def __init__(self, data=None, adapter=None):
        Abstract.__init__(self, data, adapter)
        self._table = 'beneficiary'
        self._columns = ['beneficiary_uuid', 'user_uuid', 'beneficiary_user_uuid', 'public_address', 'email',
                         'created_date', 'deactivated', 'deactivated_date']
        self._encrypt_fields = ['email']
        self._primary_key = ['beneficiary_uuid']
        self._defaults = {
            'created_date': datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            'deactivated': 0
        }

    def add_new(self, user_uuid: str, beneficiary_user_uuid: str = None, public_address: str = None, email: str = None):
        """
        Add a new beneficiary to a user
        :param user_uuid:
        :param beneficiary_user_uuid:
        :param public_address:
        :param email:
        :return:
        """
        if beneficiary_user_uuid is None and public_address is None:
            return False, 400, "error_bad_request"

        if beneficiary_user_uuid is not None:
            self.load({'user_uuid': user_uuid, 'beneficiary_user_uuid': beneficiary_user_uuid, 'deactivated': 0})
            if self.get('beneficiary_uuid') is not None:
                return False, 403, "error_exist"

            self.set_data({
                'beneficiary_uuid': str(uuid4()),
                'user_uuid': user_uuid,
                'beneficiary_user_uuid': beneficiary_user_uuid
            })
        else:
            self.load({'user_uuid': user_uuid, 'public_address': public_address, 'deactivated': 0})
            if self.get('beneficiary_uuid') is not None:
                return False, 403, "error_exist"

            self.set_data({
                'beneficiary_uuid': str(uuid4()),
                'user_uuid': user_uuid,
                'public_address': public_address,
                'email': email
            })
        self.insert()
        return True, 200, "success_beneficiary_added"

    def get_beneficiaries(self, user_uuid: str):
        """
        Return the beneficiaries of the given user
        :param user_uuid:
        :return:
        """
        filter_beneficiaries = Filter()
        filter_beneficiaries.add('deactivated', '0')
        filter_beneficiaries.add('user_uuid', user_uuid)
        beneficiaries_list = self.list(fields=['beneficiary_uuid', 'beneficiary_user_uuid', 'public_address', 'email',
                                               'created_date'],
                                       filter_object=filter_beneficiaries)
        user_beneficiaries = []
        for beneficiary in beneficiaries_list:
            user_beneficiaries.append({
                'beneficiary_uuid': beneficiary.get('beneficiary_uuid'),
                'user_uuid': beneficiary.get('beneficiary_user_uuid'),
                'created_date': beneficiary.get('created_date'),
                'email': beneficiary.get('email'),
                'public_address': beneficiary.get('public_address')
            })
        return True, 200, "success_beneficiary_retrieved", user_beneficiaries

    def remove(self, user_uuid: str, beneficiary_uuid: str):
        """
        Remove the beneficiary from the given user (deactivate him)
        :param user_uuid:
        :param beneficiary_uuid:
        :return:
        """
        self.load({'user_uuid': user_uuid, 'beneficiary_uuid': beneficiary_uuid, 'deactivated': 0})
        if self.get('beneficiary_uuid') is None:
            return False, 400, "error_not_exist"

        self.set('deactivated', 1)
        self.set('deactivated_date', datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
        self.update()
        return True, 200, "success_removed"


class TokenClaim(Abstract):
    """
    TokenClaim class extends the base class <abstract> and provides object-like access to the token_claim DB table.
    """
    def __init__(self, data=None, adapter=None):
        Abstract.__init__(self, data, adapter)
        self._table = 'token_claim'
        self._columns = ['token_claim_uuid', 'user_uuid', 'nb_token', 'tx_hash',
                         'creator_id', 'created_date', 'claimed', 'claimed_date', 'deactivated', 'deactivated_date']
        self._primary_key = ['token_claim_uuid']
        self._defaults = {
            'created_date': datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            'deactivated': 0,
            'claimed': 0
        }

    def create(self, creator_uuid: str, user_uuid: str, nb_token: float):
        """
        Create a new token claim entry for the given user
        :param creator_uuid:
        :param user_uuid:
        :param nb_token:
        :return:
        """
        self.set_data({
            'token_claim_uuid': str(uuid4()),
            'creator_id': creator_uuid,
            'user_uuid': user_uuid,
            'nb_token': nb_token
        })
        self.insert()
        return True

    def deactivate(self, user_uuid: str = None, token_claim_uuid: str = None):
        """
        Deactivate a given token claim or all token claims of the given user
        :param user_uuid:
        :param token_claim_uuid:
        :return:
        """
        if token_claim_uuid is not None:
            self.load({'token_claim_uuid': token_claim_uuid, 'claimed': 0})
            if self.get('token_claim_uuid') is None:
                return False, 400, "error_not_exist"
            self.set('deactivated', 1)
            self.set('deactivated_date', datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
            self.update()
            return True, 200, "success_deactivated"

        if user_uuid is not None:
            filter_claim = Filter()
            filter_claim.add('user_uuid', user_uuid)
            filter_claim.add('claimed', '0')
            filter_claim.add('deactivated', '0')
            active_token_claims = self.list(fields=['token_claim_uuid'], filter_object=filter_claim)
            for token_claim in active_token_claims:
                self.deactivate(token_claim_uuid=token_claim.get('token_claim_uuid'))
            return True, 200, "success_deactivated"

        return False, 400, "error_bad_request"

    def get_token_claims(self, user_uuid: str, claimed: bool = False):
        """
        Return claimable tokens for the given user
        :param user_uuid:
        :param claimed: False = return claimable tokens, True = return already claimed tokens
        :return:
        """
        filter_claim = Filter()
        filter_claim.add('user_uuid', user_uuid)
        filter_claim.add('deactivated', '0')
        if claimed is True:
            filter_claim.add('claimed', '1')
        else:
            filter_claim.add('claimed', '0')
        claims = self.list(fields=['token_claim_uuid', 'nb_token', 'tx_hash', 'created_date', 'claimed_date'],
                           filter_object=filter_claim)
        total_claim = sum(claim.get('nb_token') for claim in claims)
        total_claim = float('{:.2f}'.format(total_claim))
        return claims, total_claim

    def claim(self, user_uuid: str, user_address: str, claim_list: list):
        """
        Claim the tokens of the given token claim
        :param user_uuid:
        :param user_address:
        :param claim_list: list of claim uuid
        :return:
        """
        transactions = {}
        for claim_uuid in claim_list:
            self.load({'token_claim_uuid': claim_uuid, 'user_uuid': user_uuid})
            if self.get('nb_token') is None or self.get('claimed') == 1:
                continue

            nb_token = float(self.get('nb_token'))
            transactions[claim_uuid] = {
                'receiver': user_address,
                'nb_token': nb_token
            }

        if len(transactions) == 0:
            return False, 404, "error_bad_request", None

        polygon = Polygon()
        status, http_code, message, tx_hash = polygon.send_batch_tx(transactions=transactions)
        if status is False:
            return False, http_code, message, None

        current_date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        for claim_uuid, operation_hash in tx_hash.items():
            if operation_hash is not None:
                self.load({'token_claim_uuid': claim_uuid, 'user_uuid': user_uuid})
                self.set('tx_hash', operation_hash)
                self.set('claimed', '1')
                self.set('claimed_date', current_date)
                self.update()
            token_operation = TokenOperation()
            status_op, http_code_op, message_op = token_operation.add_operation(
                receiver_uuid=user_uuid, sender_address=env['POLYGON_PUBLIC_KEY'],
                receiver_address=user_address, token=token_operation.CAA,
                nb_token=transactions[claim_uuid].get('nb_token'), tx_hash=operation_hash)
            transactions[claim_uuid]['tx_hash'] = operation_hash
        return True, 200, "success_operation", transactions
