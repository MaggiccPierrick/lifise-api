
class OperatorType:
    AND = 'AND'
    OR = 'OR'
    EQ = 'EQ'
    NEQ = 'NEQ'
    GT = 'GT'
    GET = 'GET'
    LT = 'LT'
    LET = 'LET'
    IN = 'IN'
    INN = 'INN'
    LIKE = 'LIKE'
    IIN = 'IIN'
    NIN = 'NIN'

    _TYPE_MAPPING = {
        AND: 'AND',
        OR: 'OR',
        EQ: '=',
        NEQ: '!=',
        GT: '>',
        GET: '>=',
        LT: '<',
        LET: '<=',
        IN: 'IS NULL',
        INN: 'IS NOT NULL',
        LIKE: 'LIKE',
        IIN: 'IN',
        NIN: 'NOT IN'
    }

    @staticmethod
    def get(operator_type):
        operator = OperatorType._TYPE_MAPPING.get(operator_type)
        if not operator:
            raise ValueError('Operator Type not found: {0}'.format(operator_type))

        return operator


class Filter(object):
    """
    Filter object used for advanced DB queries with multiple conditions.

    :operator: The OperatorType that will be used when joining query conditions
    :data: Load the data provided as dict; the default operator will
           be used for generating the conditions ( OperatorType.EQ ).
    """

    def __init__(self, operator=OperatorType.AND, data=None):
        """
        :operator: The OperatorType that will be used when joining query conditions
        :data: Load the data provided as dict; the default operator will
               be used for generating the conditions ( OperatorType.EQ ).
        """

        self._unprocessed_data_values = []
        self._data = []
        self._operator = OperatorType.get(operator)

        if data:
            if not isinstance(data, dict):
                raise ValueError('Invalid data provided')
            for key, value in data.items():
                self.add(key, value)

    @property
    def data(self):
        """
        data getter
        :return: list of sets or empty list
        """
        return self._data

    @data.setter
    def data(self, data):
        """
        Apply/load a set of data on the current filter
        :param data: list pf sets e.g. :
                     [('key1', OperatorType, 'value1'),
                      ('key2', OperatorType, 'value2')]
        """
        if not isinstance(data, list) or not isinstance(data, tuple):
            raise ValueError('Invalid set of data provided')
        for filter_set in data:
            if not isinstance(filter_set, tuple) or len(filter_set) != 3:
                raise ValueError('Invalid filter data set: {0}'.format(filter_set))
            self.add(*filter_set)

    @data.deleter
    def data(self):
        """
        Reinitialize data
        """
        self._data = []
        self._unprocessed_data_values = []

    def add(self, key, value=None, operator=OperatorType.EQ):
        """
        Sets a new condition to the filter
        Add the given condition (key, value, operator) to the filter
        :param key:
        :param value:
        :param operator: OperatorType
        """
        if operator == OperatorType.IN or operator == OperatorType.INN:
            if not key:
                raise ValueError('Key cannot be empty')
            try:
                key = '`{0}`'.format(key)
            except Exception as ex:
                raise ValueError('Invalid key/value specified. Error : {0}'.format(str(ex)))
            self._data.append((key, OperatorType.get(operator)))
            return

        if not key or not value:
            raise ValueError('Key/Value cannot be empty')

        self._unprocessed_data_values.append(value)
        if operator == OperatorType.IIN or operator == OperatorType.NIN:
            if not key:
                raise ValueError('Key cannot be empty')
            if not isinstance(value, list):
                raise ValueError('Value must be a list')

        try:
            key = '`{0}`'.format(key)
            if isinstance(value, list):
                pass
            elif isinstance(value, str):
                value = "'{0}'".format(value)
            else:
                value = "{0}".format(value.encode('utf-8'))
        except Exception as ex:
            raise ValueError('Invalid key/value specified. Error : {0}'.format(str(ex)))
        self._data.append((key, OperatorType.get(operator), value))

    def _generate_sql(self, hide_data=False):
        """
        Generate filter SQL
        :param hide_data: Set to False in case you want to send the data separately to the SQL Cursor
        :return:
        """

        if not self._data:
            return ''

        conditions = []
        for filter_set in self._data:
            if filter_set[1] == 'IS NULL' or filter_set[1] == 'IS NOT NULL':
                conditions.append(' '.join(filter_set))
            elif hide_data:
                filter_set_masked = (filter_set[0], filter_set[1], '%s')
                conditions.append(' '.join(filter_set_masked))
            else:
                conditions.append(' '.join(filter_set))

        operator = ' {0} '.format(OperatorType.get(self._operator))
        sql = operator.join(conditions)
        return sql

    def get(self, nested_data=False):
        """
        Returns filter SQL including (or not) the given data.
        If the data is not included (nested) it will be returned separately
        :param nested_data: Include or not data in the query
        :return: SQL Filter and data
        """
        filter_sql = self._generate_sql(not nested_data)
        if nested_data:
            return filter_sql, None
        return filter_sql, self._unprocessed_data_values
