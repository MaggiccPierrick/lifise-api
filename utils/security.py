from hashlib import pbkdf2_hmac
from cryptography.fernet import Fernet
from uuid import uuid4


def generate_hash(data_to_hash, salt=None):
    """
    Generate the salt and the hash of the given data OR hash the data with the given salt
    :param data_to_hash:
    :param salt:
    :return:
    """
    if salt is None:
        salt = str(uuid4())
    return pbkdf2_hmac('sha512', password=data_to_hash.encode(), salt=salt.encode(), iterations=123456).hex(), salt


def encrypt(data_to_encrypt, encryption_key):
    """
    Encrypt data with the given key
    :param data_to_encrypt:
    :param encryption_key:
    :return: encrypted data
    """
    fernet = Fernet(key=encryption_key)
    data_encrypted = fernet.encrypt(data_to_encrypt)
    return data_encrypted


def decrypt(data_to_decrypt, encryption_key):
    """
    Decrypt data with the given key
    :param data_to_decrypt:
    :param encryption_key:
    :return: decrypted data
    """
    fernet = Fernet(key=encryption_key)
    data_decrypted = fernet.decrypt(data_to_decrypt)
    return data_decrypted
