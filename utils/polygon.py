from web3 import Web3
from os import environ as env
from alchemy import Alchemy, Network
from utils.log import Logger


class Polygon:
    def __init__(self):
        self.platform_address = env['POLYGON_PUBLIC_KEY']
        self.platform_private_key = env['POLYGON_PRIVATE_KEY']
        self.alchemy_api_key = env['ALCHEMY_API_KEY']
        self.max_retries = int(env['ALCHEMY_MAX_RETRIES'])
        self.rpc_node = "{0}{1}".format(env['POLYGON_RPC_NODE'], self.alchemy_api_key)
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_node))

        if env['POLYGON_NETWORK'] == 'MAINNET':
            self.network = Network.MATIC_MAINNET
            self.chain_id = 137
        else:
            self.network = Network.MATIC_MUMBAI
            self.chain_id = 80001

        self.alchemy = Alchemy(self.alchemy_api_key, self.network, max_retries=self.max_retries)
        self.default_gas = int(env['POLYGON_GAS'])
        self.log = Logger()

    def _build_tx(self, receiver_address: str, nb_token: int, gas: int = None):
        """

        :param receiver_address:
        :param nb_token:
        :param gas:
        :return:
        """
        if gas is None:
            gas = self.default_gas
        sender = Web3.toChecksumAddress(self.platform_address)
        receiver = Web3.toChecksumAddress(receiver_address)
        nonce = self.web3.eth.getTransactionCount(sender)
        tx = {
            'nonce': nonce,
            'to': receiver,
            'value': self.web3.to_wei(nb_token, 'gwei'),
            'gas': gas,
            'chainId': self.chain_id,
            'maxFeePerGas': 2000000000,
            'maxPriorityFeePerGas': 2000000000,
        }
        return tx

    def _sign_tx(self, transaction: dict):
        """
        Sign a transaction with platform private key
        :param transaction:
        :return:
        """
        try:
            signed_tx = self.web3.eth.account.sign_transaction(transaction, self.platform_private_key)
        except Exception as e:
            self.log.error("Signing transaction failed with error : {0}".format(e))
            return None
        return signed_tx

    def send_tx(self, receiver_address: str, nb_token: int, gas=None):
        """
        Sign a transaction for Polygon network
        :param receiver_address:
        :param nb_token: in gwei
        :param gas:
        :return:
        """
        transaction = self._build_tx(receiver_address=receiver_address, nb_token=nb_token, gas=gas)
        signed_tx = self._sign_tx(transaction=transaction)
        if signed_tx is None:
            return False, None
        try:
            response = self.web3.eth.send_raw_transaction(transaction=signed_tx.rawTransaction)
        except Exception as e:
            self.log.error("Sending Polygon transaction failed with error : {0}".format(e))
            return False, None

        return True, response.hex()
