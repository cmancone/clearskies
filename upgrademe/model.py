from abc import ABC, abstractmethod


class Model(ABC):
    _cursor = None
    _data = None

    def __init__(self, cursor):
        self._cursor = cursor

    @property
    @abstractmethod
    def table_name(self):
        """ Return the name of the table that the model uses for data storage """
        pass

    def __getattr__(self, attribute_name):
        # this should be adjusted to only return None for empty records if the attribute name corresponds
        # to an actual column in the table.
        if not self.exists:
            return None

        return self._data[attribute_name]

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

        data = self.columns_pre_save(data)
        data = self.pre_save(data)
        if data is None:
            raise ValueError("pre_save forgot to return the data array!")

        [sql, parameters] = self._data_to_query(data)
        self._cursor.execute(sql, parameters)
        id = self.id if self.exists else self._cursor.lastrowid

        data = self.columns_post_save(data, id)
        data = self.post_save(data, id)
        if data is None:
            raise ValueError("post_save forgot to return the data array!")

        self.data = data
        return True

    def _data_to_query(self, data):
        if self.exists:
            return self._data_to_update_query(data)
        else:
            return self._data_to_insert_query(data)

    def _data_to_update_query(self, data):
        query_parts = []
        parameters = []
        for (key, val) in data.items():
            query_parts.append(f'`{key}`=?')
            parameters.append(val)
        updates = ', '.join(query_parts)
        return [f'UPDATE {self.table_name} SET {updates} WHERE id={self.id}', parameters]

    def _data_to_insert_query(self, data):
        columns = '`' + '`, `'.join(data.keys()) + '`'
        placeholders = ', '.join(['?' for i in range(len(data))])
        return [f'INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})', data.values()]

    def columns_pre_save(self, data):
        """ Uses the column information present in the model to make any necessary changes before saving """
        return data

    def pre_save(self, data):
        """
        A hook to extend so you can provide additional pre-save logic as needed

        It is passed in the data being saved and it should return the same data with adjustments as needed
        """
        return data

    def columns_post_save(self, data, id):
        """ Uses the column information present in the model to make additional changes as needed after saving """
        return data

    def post_save(self, data, id):
        """
        A hook to extend so you can provide additional pre-save logic as needed

        It is passed in the data being saved as well as the id.  It should take action as needed and then return
        either the original data array or an adjusted one if appropriate.
        """
        return data
