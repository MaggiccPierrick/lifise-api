import pymysql
import pymysql.cursors

from threading import Thread
from queue import Queue
from os import environ as env

__all__ = ['get_connection', 'get_user_connection', 'get_singleton_user_connection', 'reset_connection']


class Adapter(Thread):
    def __init__(self, db_file):
        super(Adapter, self).__init__()
        self.db_file = db_file
        self.queue = Queue()
        self.start()

    @staticmethod
    def get_connection():
        connection = pymysql.connect(user=env['SQL_USER'], password=env['SQL_PASSWORD'], host=env['SQL_HOST'],
                                     database=env['SQL_DB_NAME'], cursorclass=pymysql.cursors.DictCursor,
                                     port=int(env['SQL_PORT']), ssl_ca=env['SQL_SSL_CERT'])
        return connection

    def run(self):
        connection = self.get_connection()
        cursor = connection.cursor()

        while True:
            query, params, response = self.queue.get()
            if query == '--close--':
                break
            cursor.execute(query, params)
            if response:
                for rec in cursor:
                    response.put(rec)
                response.put('--end--')
            else:
                connection.commit()

            self.queue.task_done()

        connection.close()

    def execute(self, query, params=None, response=None):
        self.queue.put((query, params or tuple(), response))

    def select(self, query, params=None):
        response = Queue()
        self.execute(query, params, response)

        items = []
        while True:
            rec = response.get()
            response.task_done()

            if rec == '--end--':
                break

            items.append(rec)

        return items

    def close(self):
        self.execute('--close--')


force_reset_connection = False


# used by wsgi multiprocess container
def get_connection():
    connection = pymysql.connect(user=env['SQL_USER'], password=env['SQL_PASSWORD'], host=env['SQL_HOST'],
                                 database=env['SQL_DB_NAME'], cursorclass=pymysql.cursors.DictCursor,
                                 port=int(env['SQL_PORT']), ssl_ca=env['SQL_SSL_CERT'])
    return connection


# used by wsgi multiprocess container
def get_user_connection():
    return get_connection()


def get_singleton_user_connection():
    return get_connection()


def reset_connection():
    global force_reset_connection
    force_reset_connection = True
