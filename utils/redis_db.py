import redis

from os import environ as env


class Redis:
    def __init__(self, db: int = 0):
        self.host = env['REDIS_HOST']
        self.port = int(env['REDIS_PORT'])
        self.db = db

    def get_connection(self):
        """
        Connect to Redis service
        """
        try:
            return redis.StrictRedis(host=self.host, port=self.port, db=self.db, decode_responses=True)
        except (ConnectionRefusedError, ConnectionError, ConnectionResetError, redis.ConnectionError):
            return False
