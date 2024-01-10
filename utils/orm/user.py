from uuid import uuid4
from datetime import datetime, timedelta
from os import environ as env
from random import randrange

from utils.orm.abstract import Abstract
from utils.orm.filter import Filter
from utils.security import generate_hash
from utils.email import check_email_format


class UserAccount(Abstract):
    """
    UserAccount class extends the base class <abstract> and provides object-like access to the user DB table.
    """
    def __init__(self, data=None, adapter=None):
        Abstract.__init__(self, data, adapter)
        self._table = 'user'
        self._columns = ['user_uuid', 'firstname', 'lastname', 'birthdate', 'email', 'email_hash', 'email_validated',
                         'otp_token', 'otp_expiration', 'public_address', 'magiclink_issuer', 'last_login',
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
            return False, 400, "error_firstname"
        if lastname is not None and (len(lastname) < 2 or len(lastname) > 30):
            return False, 400, "error_lastname"

        if check_email_format(email_address) is False:
            return False, 400, "error_email"

        if self.is_existing(email_address=email_address) is True:
            return False, 400, "error_exist"

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
            return False, 500, "error_user_register"

        return True, 200, "success_user_register"

    def login(self, user_uuid: str = None, magiclink_issuer: str = None):
        """
        Login the user
        :param user_uuid:
        :param magiclink_issuer:
        :return:
        """
        if user_uuid is None and magiclink_issuer is None:
            return False, 400, "error_bad_request"
        if user_uuid is not None:
            self.load({'user_uuid': user_uuid})
        else:
            self.load({'magiclink_issuer': magiclink_issuer})
        if self.get('user_uuid') is None:
            return False, 401, 'error_not_exist'
        self.set('last_login', datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
        self.update()
        return True, 200, 'success_login'

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

    def is_existing(self, email_address):
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
                       lastname: str = None, birthdate: str = None):
        """
        Update user data
        :param public_address:
        :param magiclink_issuer:
        :param firstname:
        :param lastname:
        :param birthdate:
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

        if updated is True:
            self.set('updated_date', datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
            self.update()
            return True, 200, "success_account_updated"
        else:
            return False, 400, "error_account_update"
