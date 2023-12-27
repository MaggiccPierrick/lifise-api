from uuid import uuid4
from datetime import datetime
from os import environ as env

from utils.orm.abstract import Abstract
from utils.security import generate_hash
from utils.email import check_email_format


class AdminAccount(Abstract):
    """
    AdminAccount class extends the base class <abstract> and provides object-like access to the admin DB table.
    """
    def __init__(self, data=None, adapter=None):
        Abstract.__init__(self, data, adapter)
        self._table = 'admin'
        self._columns = ['admin_uuid', 'firstname', 'lastname', 'email', 'email_hash', 'email_validated',
                         'otp_token', 'otp_expiration', 'password', 'user_salt', 'last_login',
                         'creator_id', 'created_date', 'updated_date', 'deactivated', 'deactivated_date']
        self._encrypt_fields = ['email', 'firstname', 'lastname']
        self._primary_key = ['admin_uuid']
        self._defaults = {
            'created_date': datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            'email_validated': 0,
            'deactivated': 0
        }

    def create_account(self, creator_id, email_address, firstname, lastname):
        """
        Create a new admin account
        :param creator_id:
        :param email_address:
        :param firstname:
        :param lastname:
        :return:
        """
        if len(firstname) > 30:
            return False, 400, "firstname is too long"
        if len(firstname) < 2:
            return False, 400, "firstname is too short"
        if len(lastname) > 30:
            return False, 400, "lastname is too long"
        if len(lastname) < 2:
            return False, 400, "lastname is too short"

        if check_email_format(email_address) is False:
            return False, 400, "Bad email address format"

        if self.is_existing(email_address=email_address) is True:
            return False, 400, "Email address already exists"

        password = str(uuid4())[24:]
        hash_password, unique_salt = generate_hash(password + env['APP_PASSWORD_SALT'])
        email_address_hash, email_salt = generate_hash(data_to_hash=email_address, salt=env['APP_DB_HASH_SALT'])

        user_uuid = str(uuid4())
        try:
            self.set_data({
                'creator_id': creator_id,
                'admin_uuid': user_uuid,
                'email': email_address,
                'password': hash_password,
                'user_salt': unique_salt,
                'email_hash': email_address_hash,
                'firstname': firstname,
                'lastname': lastname
            })
            self.insert()
        except Exception as e:
            self.log.error("User registration db error = {0}".format(e))
            return False, 500, "Error while registering admin"

        return True, 200, "Admin account successfully created"

    def is_existing(self, email_address=None):
        """
        Verify if the given account parameters already exist in db
        :param email_address:
        :return:
        """
        if email_address is None:
            return False

        email_address_hash, email_salt = generate_hash(data_to_hash=email_address, salt=env['APP_DB_HASH_SALT'])
        self.load({'email_hash': email_address_hash})
        if self.get('admin_uuid') is not None:
            return True
        return False

    def is_admin(self, user_uuid):
        """
        Verify if the given user uuid is an admin
        :param user_uuid:
        :return:
        """
        self.load({'admin_uuid': user_uuid})
        if self.get('admin_uuid') is not None:
            return True
        return False
