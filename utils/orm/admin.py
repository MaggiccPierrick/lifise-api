from uuid import uuid4
from datetime import datetime, timedelta
from os import environ as env
from random import randrange

from utils.orm.abstract import Abstract
from utils.orm.filter import Filter
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
        self._encrypt_fields = ['email', 'firstname', 'lastname', 'otp_token']
        self._primary_key = ['admin_uuid']
        self._defaults = {
            'created_date': datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            'email_validated': 0,
            'deactivated': 0
        }

    def create_account(self, creator_id: str, email_address: str, firstname: str, lastname: str):
        """
        Create a new admin account
        :param creator_id:
        :param email_address:
        :param firstname:
        :param lastname:
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
            return False, 500, "error_admin_creation"

        return True, 200, "success_admin_creation"

    def update_account(self, email_address: str = None, firstname: str = None, lastname: str = None,
                       old_password: str = None, new_password: str = None):
        """
        Update personal information
        :param email_address:
        :param firstname:
        :param lastname:
        :param old_password:
        :param new_password:
        :return:
        """
        updated = False
        if firstname is not None and 2 <= len(firstname) < 30:
            self.set('firstname', firstname)
            updated = True

        if lastname is not None and 2 <= len(lastname) < 30:
            self.set('lastname', lastname)
            updated = True

        if email_address is not None and check_email_format(email_address) is True:
            email_address = email_address.lower()
            if self.is_existing(email_address=email_address) is True:
                return False, 400, "error_email_exists"
            email_address_hash, email_salt = generate_hash(data_to_hash=email_address, salt=env['APP_DB_HASH_SALT'])
            self.set('email', email_address)
            self.set('email_hash', email_address_hash)
            self.set('email_validated', 0)
            updated = True

        if old_password is not None and new_password is not None:
            password_hash, password_salt = generate_hash(data_to_hash=old_password + env['APP_PASSWORD_SALT'],
                                                         salt=self.get('user_salt'))
            if self.get('password') == password_hash:
                hash_password, unique_salt = generate_hash(new_password + env['APP_PASSWORD_SALT'])
                self.set('password', hash_password)
                self.set('user_salt', unique_salt)
                updated = True

        if updated is True:
            self.set('updated_date', datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
            self.update()
            return True, 200, "success_account_updated"
        else:
            return False, 400, "error_account_update"

    def reset_password(self, email_address: str, new_password: str, reset_token: str):
        """
        Reset admin password
        :param email_address:
        :param new_password:
        :param reset_token:
        :return:
        """
        status, http_code, message = self.check_otp_token(email_address=email_address, token=reset_token)
        if status is False:
            return status, http_code, message

        hash_password, unique_salt = generate_hash(new_password + env['APP_PASSWORD_SALT'])
        self.set('password', hash_password)
        self.set('user_salt', unique_salt)
        self.set('updated_date', datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
        self.update()
        return True, 200, "success_updated"

    def is_existing(self, email_address):
        """
        Verify if the given account parameters already exist in db
        :param email_address:
        :return:
        """
        email_address_hash, email_salt = generate_hash(data_to_hash=email_address, salt=env['APP_DB_HASH_SALT'])
        filter_admin = Filter()
        filter_admin.add('email_hash', email_address_hash)
        admin_accounts = self.list(fields=['admin_uuid'], filter_object=filter_admin)
        if len(admin_accounts) > 0:
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

    def create_otp_token(self, email_address: str = None, admin_uuid: str = None):
        """
        Set a new otp token
        :param email_address:
        :param admin_uuid:
        :return:
        """
        if email_address is not None:
            if check_email_format(email_address) is False:
                return False, 400, "error_email_format"

            email_address_hash, email_salt = generate_hash(data_to_hash=email_address, salt=env['APP_DB_HASH_SALT'])
            self.load({'email_hash': email_address_hash, 'deactivated': 0})
        elif admin_uuid is not None:
            self.load({'admin_uuid': admin_uuid})

        if self.get('admin_uuid') is None:
            return False, 400, "error_not_exist"

        expiration_date = datetime.utcnow() + timedelta(seconds=int(env['APP_TOKEN_DELAY']))
        token = str(uuid4())[:8]
        self.set('otp_token', token)
        self.set('otp_expiration', expiration_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
        self.update()
        return True, 200, "success_token_set"

    def check_otp_token(self, email_address: str, token: str):
        """
        Check the otp token for the given user
        :param email_address:
        :param token:
        :return:
        """
        if check_email_format(email_address) is False:
            return False, 400, "error_email_format"

        email_address_hash, email_salt = generate_hash(data_to_hash=email_address, salt=env['APP_DB_HASH_SALT'])
        self.load({'email_hash': email_address_hash, 'deactivated': 0})
        if self.get('admin_uuid') is not None and self.get('otp_token') == token:
            if self.get('otp_expiration') < str(datetime.utcnow()):
                self.set('otp_token', None)
                self.set('otp_expiration', None)
                self.update()
                return False, 401, "error_token_expired"
            else:
                self.set('otp_token', None)
                self.set('otp_expiration', None)
                self.update()
                return True, 200, "success_token_valid"
        else:
            return False, 401, "error_token"

    def login(self, login, password, token=None):
        """
        Verify login and password and generate 2fa token or verify token if given
        :param login: login of the user (email or username)
        :param password: password of the user
        :param token: 2fa token to verify (if given)
        """
        login_hash, email_salt = generate_hash(data_to_hash=login, salt=env['APP_DB_HASH_SALT'])
        self.load({'email_hash': login_hash, 'deactivated': '0'})
        if self.get('admin_uuid') is None:
            return False, 401, "error_login"

        password_hash, password_salt = generate_hash(data_to_hash=password + env['APP_PASSWORD_SALT'],
                                                     salt=self.get('user_salt'))
        if self.get('password') == password_hash:
            if token is None:
                otp_token = '{:06}'.format(randrange(1, 10 ** 6))
                self.set('otp_token', otp_token)
                validity_date = datetime.utcnow() + timedelta(seconds=int(env['APP_TOKEN_DELAY']))
                self.set('otp_expiration', validity_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
                self.update()
                return True, 200, "success_token_set"
            else:
                current_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                if self.get('otp_token') is None:
                    return False, 401, "error_login"
                if token == self.get('otp_token'):
                    if self.get('otp_expiration') > current_time:
                        self.set('last_login', current_time)
                        self.set('otp_token', None)
                        self.set('otp_expiration', None)
                        self.set('email_validated', 1)
                        self.update()
                        return True, 200, "success_login"
                    else:
                        return False, 401, "error_token_expired"
                return False, 401, "error_login"
        else:
            return False, 401, "error_login"

    def deactivate_admin(self, admin_uuid):
        """
        Deactivate an admin user
        :param admin_uuid:
        :return:
        """
        self.load({'admin_uuid': admin_uuid})
        if self.get('admin_uuid') is not None:
            self.set('deactivated', 1)
            self.set('deactivated_date', datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
            self.update()
            return True, 200, "success_deactivated"
        return False, 400, "error_not_exist"

    def reactivate_admin(self, admin_uuid):
        """
        Reactivate an admin user
        :param admin_uuid:
        :return:
        """
        self.load({'admin_uuid': admin_uuid})
        if self.get('admin_uuid') is not None:
            self.set('deactivated', 0)
            self.set('deactivated_date', None)
            self.update()
            return True, 200, "success_reactivated"
        return False, 400, "error_not_exist"
