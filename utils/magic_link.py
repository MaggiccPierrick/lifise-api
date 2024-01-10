import json

import magic_admin.error
from magic_admin import Magic
from os import environ as env

from utils.log import Logger


class MagicLink:
    def __init__(self):
        self.secret_key = env['MAGICLINK_SECRET_KEY']
        self.retries = int(env['MAGICLINK_RETRIES'])
        self.timeout = int(env['MAGICLINK_TIMEOUT'])
        self.backoff_factor = env['MAGICLINK_FACTOR']
        self.magic = Magic(
            api_secret_key=self.secret_key,
            retries=self.retries,
            timeout=self.timeout,
            backoff_factor=self.backoff_factor,
        )
        self.token = self.magic.Token
        self.user = self.magic.User
        self.log = Logger()

    def get_user_info(self, did_token):
        """
        Return user info from MagicLink
        :param did_token:
        :return: user_data = {
                    "email": "email@domain.com",
                    "issuer": "did:ethr:0x...",
                    "oauth_provider": null,
                    "phone_number": null,
                    "public_address": "0x...",
                    "wallets":[]
                }
        """
        try:
            self.token.validate(did_token)
        except (magic_admin.error.DIDTokenExpired,
                magic_admin.error.DIDTokenMalformed,
                magic_admin.error.DIDTokenInvalid) as e:
            self.log.warning('MagicLink DID token error: {0}'.format(e))
            return False, 401, 'error_magic_link', None

        issuer = self.token.get_issuer(did_token=did_token)
        magic_response = self.user.get_metadata_by_issuer(issuer)
        user_metadata = json.loads(magic_response.content)
        if user_metadata.get('status') != 'ok':
            return False, 401, 'error_magic_link', None

        user_data = user_metadata.get('data')
        return True, 200, 'success_login', user_data
