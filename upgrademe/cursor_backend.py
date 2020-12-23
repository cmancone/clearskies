from .backend import Backend


class CursorBackend(Backend):
    _cursor = None

    def __init__(self, cursor):
        self._cursor = cursor

    def update(self, id, data, model):
        query_parts = []
        parameters = []
        for (key, val) in data.items():
            query_parts.append(f'`{key}`=?')
            parameters.append(val)
        updates = ', '.join(query_parts)

        self._cursor.execute(f'UPDATE `{model.table_name}` SET {updates} WHERE id=?', [*parameters, id])
        return self._fetch(f'SELECT * FROM `{model.table_name}` WHERE id=?', [id])

    def create(self, data, model):
        columns = '`' + '`, `'.join(data.keys()) + '`'
        placeholders = ', '.join(['?' for i in range(len(data))])

        self._cursor.execute(
            f'INSERT INTO `{model.table_name}` ({columns}) VALUES ({placeholders})',
            list(data.values())
        )

        id = self._cursor.lastrowid
        return self._fetch(f'SELECT * FROM `{model.table_name}` WHERE id=?', [id])

    def _fetch(self, query, parameters):
        self._cursor.execute(query, parameters)
        return self._cursor.next()
