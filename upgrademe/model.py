from abc import ABC, abstractmethod
from collections import OrderedDict
from .column_types import Integer


class Model(ABC):
    _columns = None
    _configured_columns = None
    _cursor = None
    _data = None
    _transformed = None

    def __init__(self, cursor, columns):
        self._cursor = cursor
        self._columns = columns
        self._transformed = {}
        self._data = {}

    @property
    def table_name(self):
        """ Return the name of the table that the model uses for data storage """
        singular = self.__class__.__name__.lower()
        return singular[:-1] + 'ies' if singular[-1] == 'y' else f'{singular}s'

    @abstractmethod
    def columns_configuration(self):
        """ Returns an ordered dictionary with the configuration for the columns """
        pass

    def all_columns(self):
        default = OrderedDict([('id', {'class': Integer})])
        default.update(self.columns_configuration())
        return default

    def columns(self):
        if self._configured_columns is None:
            self._configured_columns = self._columns.configure(self.all_columns(), self.__class__)
        return self._configured_columns

    def __getattr__(self, column_name):
        # this should be adjusted to only return None for empty records if the column name corresponds
        # to an actual column in the table.
        if not self.exists:
            return None

        if column_name not in self._transformed:
            if column_name not in self._data:
                raise KeyError(f"Unknown column '{column_name}' requested from model '{self.__class__.__name__}'")

            self._transformed[column_name] = \
                self.columns()[column_name].from_database(self._data[column_name]) \
                if column_name in self.columns() \
                else self._data[column_name]

        return self._transformed[column_name]


    @property
    def exists(self):
        return 'id' in self._data and self._data['id']

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = {} if data is None else data

    def save(self, data):
        """
        Save data to the database and update the model!

        Executes an update if the model corresponds to a record already, or an insert if not
        """
        if not len(data):
            raise ValueError("You have to pass in something to save!")
        columns = self.columns()

        data = self.columns_pre_save(data, columns)
        data = self.pre_save(data)
        if data is None:
            raise ValueError("pre_save forgot to return the data array!")

        [sql, parameters] = self._data_to_query(data, columns)
        self._cursor.execute(sql, parameters)
        id = self.id if self.exists else self._cursor.lastrowid

        data = self.columns_post_save(data, id, columns)
        data = self.post_save(data, id)
        if data is None:
            raise ValueError("post_save forgot to return the data array!")

        self._cursor.execute(f'SELECT * FROM `{self.table_name}` WHERE id=?', id)
        self._data = self._cursor.next()._asdict()
        self._transformed = {}
        return True

    def _data_to_query(self, data, columns):
        save_data = {**data}
        for column in columns.values():
            save_data = column.to_database(save_data)
            if save_data is None:
                raise ValueError(
                    f'Column {column.name} of type {column.__class__.__name__} did not return any data for to_database'
                )

        if self.exists:
            return self._data_to_update_query(save_data)
        else:
            return self._data_to_insert_query(save_data)

    def _data_to_update_query(self, data):
        query_parts = []
        parameters = []
        for (key, val) in data.items():
            query_parts.append(f'`{key}`=?')
            parameters.append(val)
        updates = ', '.join(query_parts)
        return [f'UPDATE `{self.table_name}` SET {updates} WHERE id=?', [*parameters, self.id]]

    def _data_to_insert_query(self, data):
        columns = '`' + '`, `'.join(data.keys()) + '`'
        placeholders = ', '.join(['?' for i in range(len(data))])
        return [f'INSERT INTO `{self.table_name}` ({columns}) VALUES ({placeholders})', list(data.values())]

    def columns_pre_save(self, data, columns):
        """ Uses the column information present in the model to make any necessary changes before saving """
        for column in columns.values():
            data = column.pre_save(data)
            if data is None:
                raise ValueError(
                    f'Column {column.name} of type {column.__class__.__name__} did not return any data for pre_save'
                )
        return data

    def pre_save(self, data):
        """
        A hook to extend so you can provide additional pre-save logic as needed

        It is passed in the data being saved and it should return the same data with adjustments as needed
        """
        return data

    def columns_post_save(self, data, id, columns):
        """ Uses the column information present in the model to make additional changes as needed after saving """
        for column in columns.values():
            data = column.post_save(data, id)
            if data is None:
                raise ValueError(
                    f'Column {column.name} of type {column.__class__.__name__} did not return any data for post_save'
                )
        return data

    def post_save(self, data, id):
        """
        A hook to extend so you can provide additional pre-save logic as needed

        It is passed in the data being saved as well as the id.  It should take action as needed and then return
        either the original data array or an adjusted one if appropriate.
        """
        return data
