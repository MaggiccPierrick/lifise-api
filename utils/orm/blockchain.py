from uuid import uuid4
from datetime import datetime

from utils.orm.abstract import Abstract


class TokenOperation(Abstract):
    """
    TokenOperation class extends the base class <abstract> and provides object-like access
    to the token_operation DB table.
    """
    def __init__(self, data=None, adapter=None):
        Abstract.__init__(self, data, adapter)
        self._table = 'token_operation'
        self._columns = ['token_operation_id', 'token_operation_uuid', 'sender_uuid', 'receiver_uuid', 'sender_address',
                         'receiver_address', 'token', 'nb_token', 'tx_hash', 'created_date']
        self._primary_key = ['token_operation_id']
        self._defaults = {
            'created_date': datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        }
        self.MATIC = 'MATIC'
        self.CAA = 'CAA'
        self.tokens = [self.MATIC, self.CAA]

    def add_operation(self, receiver_uuid: str, sender_address: str, receiver_address: str, token: str, nb_token: int,
                      tx_hash: str = None, sender_uuid: str = None):
        """
        Save an operation in db
        :param receiver_uuid:
        :param sender_address:
        :param receiver_address:
        :param token:
        :param nb_token:
        :param tx_hash: transaction hash, None if transaction failed
        :param sender_uuid: uuid of the user, None if tx sent by platform
        :return:
        """
        if token not in self.tokens:
            return False, 400, "error_token_unknown"

        self.set_data({
            'token_operation_uuid': str(uuid4()),
            'sender_uuid': sender_uuid,
            'receiver_uuid': receiver_uuid,
            'sender_address': sender_address,
            'receiver_address': receiver_address,
            'token': token,
            'nb_token': nb_token,
            'tx_hash': tx_hash
        })
        self.insert()
        return True, 200, "success_operation_saved"
