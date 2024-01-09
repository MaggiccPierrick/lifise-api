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
                         'otp_token', 'otp_expiration', 'public_address', 'last_login',
                         'creator_id', 'created_date', 'updated_date', 'deactivated', 'deactivated_date']
        self._encrypt_fields = ['email', 'firstname', 'lastname', 'birthdate', 'otp_token', 'public_address']
        self._primary_key = ['user_uuid']
        self._defaults = {
            'created_date': datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            'email_validated': 0,
            'deactivated': 0
        }

    def register(self, firstname: str, lastname: str, email_address: str, creator_id: str = None):
        """
        Create a new user account
        :param firstname:
        :param lastname:
        :param email_address:
        :param creator_id:
        :return:
        """
        if len(firstname) < 2 or len(firstname) > 30:
            return False, 400, "error_firstname"
        if len(lastname) < 2 or len(lastname) > 30:
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
                'otp_expiration': validity_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            })
            self.insert()
        except Exception as e:
            self.log.error("User registration db error = {0}".format(e))
            return False, 500, "error_user_register"

        return True, 200, "success_user_register"

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
