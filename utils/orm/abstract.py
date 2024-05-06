from base64 import urlsafe_b64encode
from cryptography.fernet import Fernet
from os import environ as env

from utils.orm.filter import Filter
from utils.log import Logger
from utils.orm.mysql import get_connection


class Abstract(object):
    """
    This class contains all DB operations functions.
    """

    def __init__(self, data=None, adapter=None):
        self._data = {}
        if data:
            self._data.update(data)
        self._adapter = adapter
        self._table = ''
        self._columns = []
        self._primary_key = ['rowid']
        self._encrypt_fields = []
        self._defaults = {}
        self.log = Logger()

        # load encryption module
        self.fernet = Fernet(key=urlsafe_b64encode(env['APP_DB_KEY'].encode()))

    def __getattribute__(self, key):
        try:
            return object.__getattribute__(self, key)
        except AttributeError:
            pass

        if key in self._data:
            return self._data[key]
        elif key in self._defaults:
            return self._defaults[key]

        raise AttributeError("'{0}' object has no attribute '{1}'".format(self.__class__.__name__, key))

    @property
    def data(self):
        return self._data

    def set_data(self, data):
        self._data = data
        return self

    def add_data(self, data):
        self._data.update(data)
        return self

    def set(self, key, value):
        self._data[key] = value
        return self

    def get(self, key):
        if key in self._data:
            return self._data[key]
        elif key in self._defaults:
            return self._defaults[key]

        return None

    def set_adapter(self, adapter):
        self._adapter = adapter

    def get_adapter(self):
        self._adapter = get_connection()
        return self._adapter

    def load(self, conditions):
        columns = []
        for column in self._columns:
            columns.append('`%s`' % column)

        where = []
        data = []
        for column in conditions:
            if conditions[column] is None or conditions[column] == 'NULL':
                where.append("`{0}` IS NULL".format(column))
            else:
                where.append("`{0}` = %s".format(column))
                data.append(conditions[column])

        query = 'SELECT %s FROM %s WHERE %s' % (', '.join(columns), self._table, ' AND '.join(where))
        result = self._execute(query, data)

        if result:
            for column in self._columns:
                if column in self._encrypt_fields:
                    if result[column] is not None:
                        self.set(column, self.fernet.decrypt(result[column].encode()).decode())
                    else:
                        self.set(column, None)
                else:
                    self.set(column, result[column])

    def insert(self):
        """
        Insert data in database
        :return:
        """
        columns = []
        values = []
        data = []
        for column in self._columns:
            if self.get(column) or self.get(column) == 0:
                columns.append('`%s`' % column)
                values.append("%s")
                if column in self._encrypt_fields and self.get(column) is not None:
                    data.append(self.fernet.encrypt(self.get(column).encode()))
                else:
                    data.append(self.get(column))

        query = 'INSERT INTO `%s`(%s) VALUES(%s)' % (self._table, ', '.join(columns), ', '.join(values))
        self._run(query, data)
        return self

    def update(self):
        columns = []
        data = []
        for column in self._columns:
            if column in self._encrypt_fields and self.get(column) is not None:
                value = self.fernet.encrypt(self.get(column).encode()).decode()
            else:
                value = self.get(column)
            columns.append('`{0}` = %s'.format(column))
            data.append(value)

        where = []
        for column in self._primary_key:
            where.append('`{0}` = %s'.format(column))
            data.append(self.get(column))

        query = 'UPDATE `%s` SET %s WHERE %s' % (self._table, ', '.join(columns), ' AND '.join(where))
        self._run(query, data)

    def delete(self):
        where = []
        data = []
        for column in self._primary_key:
            where.append('`{0}` = %s'.format(column))
            data.append(self.get(column))

        query = 'DELETE FROM `%s` WHERE %s' % (self._table, ' AND '.join(where))
        self._run(query, data)

    def delete_list(self, filter_object=None):
        filter_sql = ''
        data = []
        if filter_object and isinstance(filter_object, Filter):
            filter_sql, data = filter_object.get()
        query = 'DELETE FROM `%s`' % self._table
        if filter_sql:
            query = '{0} WHERE {1}'.format(query, filter_sql)
        self._run(query, data)

    def count(self, filter_object=None):
        filter_sql = ''
        data = []
        if filter_object and isinstance(filter_object, Filter):
            filter_sql, data = filter_object.get()

        query = "SELECT COUNT(*) as nb FROM %s" % self._table
        if filter_sql:
            query = '{0} WHERE {1}'.format(query, filter_sql)
        ret_data = self._execute(query, data, True)
        if ret_data:
            return ret_data[0].get('nb')
        else:
            return 0

    def increment_column(self, filter_object, column, number):
        """
        Increment the given column by the given number
        :param filter_object:
        :param column:
        :param number:
        :return:
        """
        filter_sql = ''
        data = []
        if filter_object and isinstance(filter_object, Filter):
            filter_sql, data = filter_object.get()

        query = "UPDATE %s SET %s = %s + %d" % (self._table, column, column, number)
        if filter_sql:
            query = '{0} WHERE {1}'.format(query, filter_sql)
        self._run(query, data)

    def max(self, field, filter_object=None):
        """
        return the table entry with the maximum value of the given field
        :param field:
        :param filter_object: Filter Object (instance of class filter.Filter)
        :return:
        """
        filter_sql = ''
        data = []
        if filter_object and isinstance(filter_object, Filter):
            filter_sql, data = filter_object.get()

        query = 'SELECT MAX({0}) FROM {1}'.format(field, self._table)
        if filter_sql:
            query = '{0} WHERE {1}'.format(query, filter_sql)
            result = self._execute(query, data, True)[0]
        else:
            result = self._execute(query)
        return result.get('MAX({0})'.format(field))

    def sum(self, field, filter_object=None):
        """
        return the sum of filtered rows for the given field
        :param field:
        :param filter_object: Filter Object (instance of class filter.Filter)
        :return:
        """
        filter_sql = ''
        data = []
        if filter_object and isinstance(filter_object, Filter):
            filter_sql, data = filter_object.get()

        query = 'SELECT SUM({0}) as sum_score FROM {1}'.format(field, self._table)
        if filter_sql:
            query = '{0} WHERE {1}'.format(query, filter_sql)
            result = self._execute(query, data, True)[0]
        else:
            result = self._execute(query)
        return result.get('sum_score')

    def list(self, fields=None, filter_object=None, limit=0, order=None, asc='ASC', group_by=None, distinct=False,
             random=False):
        """
        List all or only the given fields of entries of the DB table.
        :param fields: List with column names or None (all the fields will be fetched)
        :param filter_object: Filter Object (instance of class filter.Filter)
        :param limit: maximum number of entries to be fetched (all if 0)
        :param order: field to order by
        :param asc: order by 'ASC' or 'DESC'
        :param group_by: field to group by
        :param distinct: select distinct fields values
        :param random: select nb random rows from the table (nb = limit)
        :return: List of entries
        """
        valid_fields = []
        if not fields:
            for field in self._columns:
                valid_fields.append('`{0}`'.format(field))
        else:
            for field in fields:
                if field in self._columns:
                    valid_fields.append('`{0}`'.format(field))

        filter_sql = ''
        data = []
        if filter_object and isinstance(filter_object, Filter):
            filter_sql, data = filter_object.get()

        if distinct:
            query = 'SELECT DISTINCT({0}) FROM {1}'.format(', '.join(valid_fields), self._table)
        else:
            query = 'SELECT {0} FROM {1}'.format(', '.join(valid_fields), self._table)
        if filter_sql:
            query = '{0} WHERE {1}'.format(query, filter_sql)
        if group_by is not None:
            if isinstance(group_by, list):
                group_by = ', '.join(group_by)
            query = "{0} GROUP BY {1}".format(query, group_by)
        if order is not None:
            if isinstance(order, list):
                order = ', '.join(order)
            query = "{0} ORDER BY {1} {2}".format(query, order, asc)
        elif random is True:
            query = "{0} ORDER BY RAND()".format(query)
        if limit is not None and limit != 0:
            query = '{0} LIMIT {1}'.format(query, limit)
        result = self._execute(query, data, True)

        # Decrypt encrypted fields
        if len(self._encrypt_fields) > 0:
            for result_line in result:
                for result_column, result_value in result_line.items():
                    if result_column in self._encrypt_fields and result_value is not None:
                        result_line[result_column] = self.fernet.decrypt(result_value.encode()).decode()

        return list(result)

    def find(self, filter_object=None):
        """
        Find all the entries matching with the specified filters and return their primary keys.
        :param filter_object: Filter Object (instance of class filter.Filter)
        :return: List of entries (primary keys)
        """
        filter_sql = ''
        data = []
        if filter_object and isinstance(filter_object, Filter):
            filter_sql, data = filter_object.get()

        fields = ['`{0}`'.format(field) for field in self._primary_key]
        query = 'SELECT {0} FROM {1}'.format(', '.join(fields), self._table)
        if filter_sql:
            query = '{0} WHERE {1}'.format(query, filter_sql)

        result = self._execute(query, data, True)
        # Decrypt encrypted fields
        if len(self._encrypt_fields) > 0:
            for result_line in result:
                for result_column, result_value in result_line.items():
                    if result_column in self._encrypt_fields and result_value is not None:
                        result_line[result_column] = self.fernet.decrypt(result_value.encode()).decode()
        return list(result)

    def _execute(self, query, data=None, fetchall=False):
        # renew adapter
        self.get_adapter()
        cursor = self._adapter.cursor()
        if data is not None:
            cursor.execute(query, tuple(data))
        else:
            cursor.execute(query)

        if fetchall:
            return cursor.fetchall()

        return cursor.fetchone()

    def _run(self, query, data):
        # renew adapter
        self.get_adapter()
        cursor = self._adapter.cursor()
        cursor.execute(query, tuple(data))
        last_rowid = cursor.lastrowid
        self._adapter.commit()
        return last_rowid

    '''
    @staticmethod
    def _parse_data(data):
        result = None
        if isinstance(data, list):
            result = []
            for row in data:
                if isinstance(row, Row):
                    result.append(dict(row))
        elif isinstance(data, Row):
            result = dict(Row)

        return result
    '''
