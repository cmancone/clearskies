from .backend import Backend


class CursorBackend(Backend):
    _cursor = None

    _allowed_configs = [
        'table_name',
        'wheres',
        'sorts',
        'group_by_column',
        'limit_start',
        'limit_length',
        'selects',
        'joins',
    ]

    _required_configs = [
        'table_name',
    ]

    def __init__(self, cursor):
        self._cursor = cursor

    def configure(self):
        pass

    def update(self, id, data, model):
        query_parts = []
        parameters = []
        for (key, val) in data.items():
            query_parts.append(f'`{key}`=?')
            parameters.append(val)
        updates = ', '.join(query_parts)

        self._cursor.execute(f'UPDATE `{model.table_name}` SET {updates} WHERE id=?', [*parameters, id])

        self.iterator({
            'table_name': model.table_name,
            'wheres': [{'parsed': 'id=?', 'values': [id]}]
        })
        return self.next()

    def create(self, data, model):
        columns = '`' + '`, `'.join(data.keys()) + '`'
        placeholders = ', '.join(['?' for i in range(len(data))])

        self._cursor.execute(
            f'INSERT INTO `{model.table_name}` ({columns}) VALUES ({placeholders})',
            list(data.values())
        )

        self.iterator({
            'table_name': model.table_name,
            'wheres': [{'parsed': 'id=?', 'values': [self._cursor.lastrowid]}]
        })
        return self.next()

    def delete(self, id, model):
        self._cursor.execute(
            f'DELETE FROM `{model.table_name}` WHERE id=?',
            [id]
        )
        return True

    def count(self, configuration):
        configuration = self._check_query_configuration(configuration)
        [query, parameters] = self.as_count_sql(configuration)
        self._cursor.execute(query, parameters)
        result = self._cursor.next()
        return result[0] if type(result) == tuple else result['count']

    def iterator(self, configuration):
        configuration = self._check_query_configuration(configuration)
        [query, parameters] = self.as_sql(configuration)
        self._cursor.execute(query, parameters)
        return self

    def next(self):
        result = self._cursor.next()
        if result is None:
            raise StopIteration()
        return result

    def as_sql(self, configuration):
        [wheres, parameters] = self._conditions_as_wheres_and_parameters(configuration['wheres'])
        select = configuration['selects'] if configuration['selects'] else '*'
        joins = (' ' + ' '.join(configuration['joins'])) if configuration['joins'] else ''
        if configuration['sorts']:
            order_by = ' ORDER BY ' + ', '.join(map(lambda sort: '`%s` %s' % (sort['column'], sort['direction']), configuration['sorts']))
        else:
            order_by = ''
        group_by = ' GROUP BY `' + configuration['group_by_column'] + '`' if configuration['group_by_column'] else ''
        limit = f' LIMIT {configuration["limit_start"]}, {configuration["limit_length"]}' if configuration['limit_start'] else ''
        return [
            f'SELECT {select} FROM `{configuration["table_name"]}`{joins}{wheres}{group_by}{order_by}{limit}'.strip(),
            parameters
        ]

    def as_count_sql(self, configuration):
        # note that this won't work if we start including a HAVING clause
        [wheres, parameters] = self._conditions_as_wheres_and_parameters(configuration['wheres'])
        # we also don't currently support parameters in the join clause - I'll probably need that though
        joins = (' ' + ' '.join(filter(lambda join: 'LEFT JOIN' not in join, configuration['joins']))) if configuration['joins'] else ''
        if not configuration['group_by_column']:
            query = f'SELECT COUNT(*) AS count FROM `{configuration["table_name"]}`{joins}{wheres}'
        else:
            query = f'SELECT COUNT(SELECT 1 FROM `{configuration["table_name"]}`{joins}{wheres} GROUP BY `{configuration["group_by_column"]}`) AS count'
        return [query, parameters]

    def _conditions_as_wheres_and_parameters(self, conditions):
        if not conditions:
            return ['', []]

        parameters = []
        where_parts = []
        for condition in conditions:
            parameters.extend(condition['values'])
            where_parts.append(condition['parsed'])
        return [' WHERE ' + ' AND '.join(where_parts), parameters]

    def _check_query_configuration(self, configuration):
        for key in configuration.keys():
            if key not in self._allowed_configs:
                raise KeyError(
                    f"CursorBackend does not support config '{key}'. You may be using the wrong backend"
                )

        for key in self._required_configs:
            if key not in configuration:
                raise KeyError(f'Missing required configuration key {key}')

        for key in self._allowed_configs:
            if not key in configuration:
                configuration[key] = [] if key[-1] == 's' else ''
        return configuration
