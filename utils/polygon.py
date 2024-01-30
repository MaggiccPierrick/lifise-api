from web3 import Web3
from os import environ as env
from alchemy import Alchemy, Network, AssetTransfersCategory, exceptions
from web3.middleware import geth_poa_middleware
from datetime import datetime

from utils.log import Logger

'''
def create_wallet():
    """
    Create eth address
    :return:
    """
    from eth_account import Account
    import secrets
    private = secrets.token_hex(32)
    private_key = "0x" + private
    wallet = Account.from_key(private_key)
    public_address = wallet.address
    return private_key, public_address
'''


class Polygon:
    def __init__(self):
        self.platform_address = env['POLYGON_PUBLIC_KEY']
        self.platform_private_key = env['POLYGON_PRIVATE_KEY']
        self.caa_contract = env['POLYGON_CAA_CONTRACT']
        self.caa_decimals = int(env['POLYGON_CAA_DECIMALS'])
        self.caa_contract_abi = [{
            'constant': False,
            'inputs': [{'name': '_to', 'type': 'address'}, {'name': '_value', 'type': 'uint256'}],
            'name': 'transfer',
            'outputs': [{'name': '', 'type': 'bool'}],
            'type': 'function'
        }]

        self.alchemy_api_key = env['ALCHEMY_API_KEY']
        self.max_retries = int(env['ALCHEMY_MAX_RETRIES'])
        self.rpc_node = "{0}{1}".format(env['POLYGON_RPC_NODE'], self.alchemy_api_key)
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_node))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        if env['POLYGON_NETWORK'] == 'MAINNET':
            self.network = Network.MATIC_MAINNET
            self.chain_id = 137
        else:
            self.network = Network.MATIC_MUMBAI
            self.chain_id = 80001

        self.alchemy = Alchemy(self.alchemy_api_key, self.network, max_retries=self.max_retries)
        self.default_gas = int(env['POLYGON_GAS'])
        self.log = Logger()

    def _build_matic_tx(self, receiver_address: str, nb_token: int, gas: int = None) -> dict:
        """
        Build MATIC transaction
        :param receiver_address:
        :param nb_token:
        :param gas:
        :return:
        """
        if gas is None:
            gas = self.default_gas
        # sender = Web3.toChecksumAddress(self.platform_address)
        receiver = Web3.toChecksumAddress(receiver_address)
        # nonce = self.w3.eth.getTransactionCount(sender)
        current_datetime = datetime.utcnow()
        nonce = int(datetime.timestamp(current_datetime) * 1000000)
        tx = {
            'nonce': nonce,
            'to': receiver,
            'value': self.w3.to_wei(nb_token, 'gwei'),
            'gas': gas,
            'chainId': self.chain_id,
            'maxFeePerGas': 2000000000,
            'maxPriorityFeePerGas': 2000000000,
        }
        return tx

    def _build_erc20_tx(self, receiver_address: str, nb_token: float):
        """
        Build ERC20 token transaction
        :param receiver_address:
        :param nb_token:
        :return:
        """
        # sender = Web3.toChecksumAddress(self.platform_address)
        receiver = Web3.toChecksumAddress(receiver_address)
        # nonce = self.w3.eth.getTransactionCount(sender)
        current_datetime = datetime.utcnow()
        nonce = int(datetime.timestamp(current_datetime) * 1000000)
        contract_address = Web3.toChecksumAddress(self.caa_contract)
        contract = self.w3.eth.contract(address=contract_address, abi=self.caa_contract_abi)
        tx = {
            'nonce': nonce,
            'gas': 2000000,
            'chainId': self.chain_id
        }
        nb_token = int(nb_token * pow(10, self.caa_decimals))
        transaction = contract.functions.transfer(receiver, nb_token).buildTransaction(tx)
        return transaction

    def _sign_tx(self, transaction: dict):
        """
        Sign a transaction with platform private key
        :param transaction:
        :return:
        """
        try:
            signed_tx = self.w3.eth.account.sign_transaction(transaction, self.platform_private_key)
        except Exception as e:
            self.log.error("Signing transaction failed with error : {0}".format(e))
            return None
        return signed_tx

    def send_tx(self, receiver_address: str, nb_token: int, gas: int = None):
        """
        Send MATIC to given address
        :param receiver_address:
        :param nb_token: in gwei
        :param gas:
        :return:
        """
        transaction = self._build_matic_tx(receiver_address=receiver_address, nb_token=nb_token, gas=gas)
        signed_tx = self._sign_tx(transaction=transaction)
        if signed_tx is None:
            return False, None
        try:
            response = self.w3.eth.send_raw_transaction(transaction=signed_tx.rawTransaction)
        except Exception as e:
            self.log.error("Sending Polygon transaction failed with error : {0}".format(e))
            return False, None

        return True, response.hex()

    def send_erc20(self, receiver_address: str, nb_token: float):
        """
        Send ERC20 token to given address
        :param receiver_address:
        :param nb_token:
        :return:
        """
        transaction = self._build_erc20_tx(receiver_address=receiver_address, nb_token=nb_token)
        signed_tx = self._sign_tx(transaction=transaction)
        try:
            tx_hash = self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        except Exception as e:
            self.log.error(f"Error sending transaction: {e}")
            return False, None

        return True, tx_hash.hex()

    def _get_contract_metadata(self, contract_address: str) -> dict:
        """
        Return contract metadata
        :param contract_address:
        :return: {
          "name": "CaaEURO Stablecoin",
          "symbol": "CaaEURO",
          "decimals": 6,
          "logo": null
        }
        """
        token_metadata = self.alchemy.core.get_token_metadata(contract_address=contract_address)
        return {
            'address': contract_address,
            'name': token_metadata.name,
            'symbol': token_metadata.symbol,
            'decimals': token_metadata.decimals,
            'logo': token_metadata.logo
        }

    def get_balance(self, address: str) -> dict:
        """
        Return MATIC and contracts balances of the given address
        :param address:
        :return:
        """
        matic_balance = self.w3.eth.get_balance(address)
        matic_balance = matic_balance / pow(10, 18)

        token_metadata = self._get_contract_metadata(contract_address=self.caa_contract)
        contract_balance = 0
        if len(token_metadata.get('name')) > 0 and token_metadata.get('decimals') is not None:
            token_balances = self.alchemy.core.get_token_balances(address=address, data=[self.caa_contract])
            token_balances = token_balances.get('token_balances')
            for token_balance in token_balances:
                contract_address = token_balance.contract_address
                if contract_address == self.caa_contract:
                    contract_balance = token_balance.token_balance
                    contract_balance = int(contract_balance, base=16)
                    contract_balance = contract_balance / pow(10, token_metadata.get('decimals'))

        return {
            'token_metadata': token_metadata,
            'matic': matic_balance,
            'token_balance': contract_balance
        }

    def get_operations(self, address: str, in_page_key: str = None, out_page_key: str = None):
        """
        Return CAA operations of the address
        :param address:
        :param in_page_key:
        :param out_page_key:
        :return:
        """
        category = [AssetTransfersCategory.ERC20]
        operations = []
        try:
            out_operations = self.alchemy.core.get_asset_transfers(from_address=address, category=category,
                                                                   contract_addresses=[self.caa_contract],
                                                                   with_metadata=True, order='desc',
                                                                   max_count=15, page_key=out_page_key)
        except exceptions.AlchemyError:
            return False, 400, "error_bad_request", None, None, None

        out_page_key = out_operations.get('page_key')
        out_transfers = out_operations.get('transfers')
        for transfer in out_transfers:
            operations.append({
                'hash': transfer.hash,
                'from': transfer.frm,
                'to': transfer.to,
                'value': transfer.value,
                'asset': transfer.asset,
                'block': int(transfer.block_num, 16),
                'block_time': transfer.metadata.block_timestamp
            })

        try:
            in_operations = self.alchemy.core.get_asset_transfers(to_address=address, category=category,
                                                                  contract_addresses=[self.caa_contract],
                                                                  with_metadata=True, order='desc',
                                                                  max_count=15, page_key=in_page_key)
        except exceptions.AlchemyError:
            return False, 400, "error_bad_request", None, None, None

        in_page_key = in_operations.get('page_key')
        in_transfers = in_operations.get('transfers')
        for transfer in in_transfers:
            operations.append({
                'hash': transfer.hash,
                'from': transfer.frm,
                'to': transfer.to,
                'value': transfer.value,
                'asset': transfer.asset,
                'block': int(transfer.block_num, 16),
                'block_time': transfer.metadata.block_timestamp
            })
        operations = sorted(operations, key=lambda x: x['block'], reverse=True)
        return True, 200, "success_operations", operations, out_page_key, in_page_key
