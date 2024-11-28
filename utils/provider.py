from web3 import Web3
from os import environ as env
from alchemy import Alchemy, Network, AssetTransfersCategory, exceptions
from web3.middleware import geth_poa_middleware

from utils.redis_db import Redis
from utils.scaleway import SecretManager
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


def lock_nonce(address: str, nonce: int) -> bool:
    """
    Set nonce to make tx and lock send feature for the given address
    :param address:
    :param nonce:
    :return: boolean
    """
    redis_db = Redis(db=1)
    redis_connect = redis_db.get_connection()
    if redis_connect is False:
        return False
    current_nonce = redis_connect.get(address)
    if current_nonce is not None:
        return False
    redis_connect.set(address, str(nonce), ex=30)
    return True


def unlock_nonce(address: str) -> bool:
    """
    Remove the nonce from lock for the given address
    :param address:
    :return: boolean
    """
    redis = Redis(db=1)
    redis_connect = redis.get_connection()
    if redis_connect is False:
        return False
    redis_connect.delete(address)
    return True


class Provider:
    def __init__(self):
        self.platform_address = env['ADMIN_WALLET_PUBLIC_KEY']
        self.euro_lfs_contract = env['PROVIDER_TOKEN_EUROLFS_CONTRACT']
        self.euro_lfs_decimals = int(env['PROVIDER_TOKEN_EUROLFS_DECIMALS'])
        self.euro_lfs_contract_abi = [
        {"constant":True,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"type":"function"},
        {"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},
        {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
        {"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},
        {
            'constant': False,
            'inputs': [{'name': '_to', 'type': 'address'}, {'name': '_value', 'type': 'uint256'}],
            'name': 'transfer',
            'outputs': [{'name': '', 'type': 'bool'}],
            'type': 'function'
        }]

        self.alchemy_api_key = env['ALCHEMY_API_KEY']
        self.max_retries = int(env['ALCHEMY_MAX_RETRIES'])
        # self.rpc_node = "{0}{1}".format(env['PROVIDER_RPC_NODE'], self.alchemy_api_key)
        self.rpc_node = env['PROVIDER_RPC_NODE']
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_node))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        if env['PROVIDER_NETWORK'] == 'MAINNET':
            self.network = Network.AVALANCHE_MAINNET
            self.chain_id = 137
        else:
            # self.network = Network.MATIC_MAINNET
            self.network = Network.ETH_MAINNET
            self.chain_id = int(env['PROVIDER_CHAIN_ID'])

        self.erc20_stable_token_contract = self.w3.eth.contract(address=self.euro_lfs_contract, abi=self.euro_lfs_contract_abi)

        self.alchemy = Alchemy(self.alchemy_api_key, self.network, max_retries=self.max_retries)
        self.default_gas = int(env['PROVIDER_GAS'])
        self.log = Logger()

    def _build_w3_tx(self, receiver_address: str, nb_token: int, nonce: int, gas: int = None):
        """
        Build web3 transaction
        :param receiver_address:
        :param nb_token:
        :param nonce:
        :param gas:
        :return:
        """
        if gas is None:
            gas = self.default_gas
        receiver = Web3.to_checksum_address(receiver_address)

        # TODO: Check error
        # Always have error = {'code': -32000, 'message': 'insufficient funds for transfer'} but funds are on the wallet 
        # and the transaction can be proceed without estimate gas call
        #
        # tx = {
        #     'nonce': nonce,
        #     'to': receiver,
        #     'value': self.w3.to_wei(nb_token, 'gwei'),
        #     'gas': gas,
        #     'chainId': self.chain_id,
        #     # 'maxFeePerGas': 85000000000,
        #     # 'maxPriorityFeePerGas': 85000000000,
        #     'maxFeePerGas': self.w3.to_wei(1, 'gwei'),
        #     'maxPriorityFeePerGas': self.w3.to_wei(1, 'gwei'),
        # }
        # try:
        #     gas = self.w3.eth.estimate_gas(transaction=tx)
        # except ValueError as e:
        #     self.log.error("Failed to estimate gas fees, error = {0}".format(e))
        #     print("Failed to estimate gas fees, error = {0}".format(e))
        #     return False

        gas_price = self.w3.eth.gas_price + 1000
        self.log.debug(gas_price)

        tx = {
            'nonce': nonce,
            'to': receiver,
            'value': self.w3.to_wei(nb_token, 'gwei'),
            'gas': gas,
            'chainId': self.chain_id,
            'maxFeePerGas': gas_price,
            'maxPriorityFeePerGas': Web3.to_wei(1, 'gwei'),
        }
        return tx

    def _build_erc20_tx(self, receiver_address: str, nb_token: float, nonce: int):
        """
        Build ERC20 token transaction
        :param receiver_address:
        :param nb_token:
        :param nonce:
        :return:
        """
        receiver = Web3.to_checksum_address(receiver_address)
        sender = Web3.to_checksum_address(self.platform_address)
        contract_address = Web3.to_checksum_address(self.euro_lfs_contract)
        contract = self.w3.eth.contract(address=contract_address, abi=self.euro_lfs_contract_abi)
        tx = {
            'chainId': self.chain_id,
            'from': sender,
            'nonce': nonce,
            'gasPrice': self.w3.eth.gasPrice,
        }
        nb_token = int(nb_token * pow(10, self.euro_lfs_decimals))
        unsigned_txn = contract.functions.transfer(receiver, nb_token).build_transaction(tx)
        return unsigned_txn

    def _sign_tx(self, transaction: dict):
        """
        Sign a transaction with platform private key
        :param transaction:
        :return:
        """
        # secret = SecretManager()
        # secrets = secret.get_secrets(secret_id=env['ADMIN_WALLET_PRIVATE_KEY'])
        # if secrets is False or secrets.get('private_key') is None:
        #     self.log.error("Failed to load private key")
        #     print("Failed to load private key")
        #     return None
        try:
            # signed_tx = self.w3.eth.account.sign_transaction(transaction, secrets.get('private_key'))
            signed_tx = self.w3.eth.account.sign_transaction(transaction, env['ADMIN_WALLET_PRIVATE_KEY'])
        except Exception as e:
            self.log.error("Signing transaction failed with error : {0}".format(e))
            return None
        return signed_tx

    def send_native_token(self, receiver_address: str, nb_token: int, gas: int = None):
        """
        Send Native Token to given address
        :param receiver_address:
        :param nb_token: in gwei
        :param gas:
        :return:
        """
        sender = Web3.to_checksum_address(self.platform_address)
        nonce = self.w3.eth.get_transaction_count(sender, 'pending')
 
        # locked = lock_nonce(address=self.platform_address, nonce=nonce)
        # if locked is False:
        #     return False, None

        transaction = self._build_w3_tx(receiver_address=receiver_address, nb_token=nb_token, nonce=nonce, gas=gas)
        if transaction is False:
            return False, None
        signed_tx = self._sign_tx(transaction=transaction)
        if signed_tx is None:
            return False, None
        try:
            response = self.w3.eth.send_raw_transaction(transaction=signed_tx.rawTransaction)
        except Exception as e:
            self.log.error("Sending native token transaction failed with error : {0}".format(e))
            return False, None

        # unlock_nonce(address=self.platform_address)
        return True, response.hex()

    def send_erc20(self, receiver_address: str, nb_token: float, nonce: int):
        """
        Send ERC20 token to given address
        :param receiver_address:
        :param nb_token:
        :param nonce:
        :return:
        """
        transaction = self._build_erc20_tx(receiver_address=receiver_address, nb_token=nb_token, nonce=nonce)
        signed_tx = self._sign_tx(transaction=transaction)
        if signed_tx is None:
            return False, None
        try:
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        except Exception as e:
            self.log.error(f"Error sending transaction: {e}")
            return False, None

        return True, tx_hash.hex()

    def send_batch_tx(self, transactions: dict):
        """
        Send a batch of operations and lock feature
        :param transactions: {tx_uuid: "receiver": "", "nb_token": 10}
        :return:
        """
       
        sender = Web3.to_checksum_address(self.platform_address)
        nonce = self.w3.eth.get_transaction_count(sender, 'pending')
        # locked = lock_nonce(address=self.platform_address, nonce=nonce)
        # if locked is False:
        #     return False, 503, "error_wait_retry", None

        transactions_hash = {}
        for tx_uuid, tx_info in transactions.items():
            status, tx_hash = self.send_erc20(receiver_address=tx_info.get('receiver'),
                                              nb_token=tx_info.get('nb_token'), nonce=nonce)
            nonce += 1
            transactions_hash[tx_uuid] = tx_hash



        # unlock_nonce(address=self.platform_address)
        return True, 200, "success_operation", transactions_hash

    def _get_contract_metadata(self, contract_address: str) -> dict:
        """
        Return contract metadata
        :param contract_address:
        :return: {
          "name": "EuroLFS Stablecoin",
          "symbol": "EUROLFS",
          "decimals": 6,
          "logo": null
        }
        """
        # token_metadata = self.alchemy.core.get_token_metadata(contract_address=contract_address)

        token_name = self.erc20_stable_token_contract.functions.name().call()
        token_symbol = self.erc20_stable_token_contract.functions.symbol().call()
        token_decimals = self.erc20_stable_token_contract.functions.decimals().call()

        return {
            'address': contract_address,
            # 'name': token_metadata.name,
            # 'symbol': token_metadata.symbol,
            # 'decimals': token_metadata.decimals,
            # 'logo': token_metadata.logo
            'name': token_name,
            'symbol': token_symbol,
            'decimals': token_decimals,
        }

    def get_balance(self, address: str) -> dict:
        """
        Return Native token and contracts balances of the given address
        :param address:
        :return:
        """
        native_token_balance = self.w3.eth.get_balance(address)
        native_token_balance = native_token_balance / pow(10, 18)

        token_metadata = self._get_contract_metadata(contract_address=self.euro_lfs_contract)
        contract_balance = 0
        if len(token_metadata.get('name')) > 0 and token_metadata.get('decimals') is not None:
            
            # token_balances = self.alchemy.core.get_token_balances(address=address, data=[self.euro_lfs_contract])
            # token_balances = token_balances.get('token_balances')

            # for token_balance in token_balances:
            #     contract_address = token_balance.contract_address
            #     if contract_address == self.euro_lfs_contract:
            #         contract_balance = token_balance.token_balance
            #         contract_balance = int(contract_balance, base=16)
            #         contract_balance = contract_balance / pow(10, token_metadata.get('decimals'))

            contract_balance = self.erc20_stable_token_contract.functions.balanceOf(address).call()
            contract_balance = contract_balance / pow(10, token_metadata.get('decimals'))

        return {
            'token_metadata': token_metadata,
            'native_token': native_token_balance,
            'token_balance': contract_balance
        }

    def get_operations(self, address: str, in_page_key: str = None, out_page_key: str = None):
        """
        Return EUROLFS operations of the address
        :param address:
        :param in_page_key:
        :param out_page_key:
        :return:
        """
        category = [AssetTransfersCategory.ERC20]
        operations = []
        try:
            out_operations = self.alchemy.core.get_asset_transfers(from_address=address, category=category,
                                                                   contract_addresses=[self.euro_lfs_contract],
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
                                                                  contract_addresses=[self.euro_lfs_contract],
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
        return True, 200, "success_operation", operations, out_page_key, in_page_key
