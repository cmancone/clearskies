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
        'model_columns',
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
            query_parts.append(f'`{key}`=%s')
            parameters.append(val)
        updates = ', '.join(query_parts)

        self._cursor.execute(f'UPDATE `{model.table_name}` SET {updates} WHERE id=%s', tuple([*parameters, id]))

        results = self.records({
            'table_name': model.table_name,
            'wheres': [{'parsed': 'id=%s', 'values': [id]}]
        }, model)
        return results[0]

    def create(self, data, model):
        columns = '`' + '`, `'.join(data.keys()) + '`'
        placeholders = ', '.join(['%s' for i in range(len(data))])

        self._cursor.execute(
            f'INSERT INTO `{model.table_name}` ({columns}) VALUES ({placeholders})',
            tuple(data.values())
        )

        results = self.records({
            'table_name': model.table_name,
            'wheres': [{'parsed': 'id=%s', 'values': [self._cursor.lastrowid]}]
        }, model)
        return results[0]

    def delete(self, id, model):
        self._cursor.execute(
            f'DELETE FROM `{model.table_name}` WHERE id=%s',
            (id,)
        )
        return True

    def count(self, configuration, model):
        configuration = self._check_query_configuration(configuration)
        [query, parameters] = self.as_count_sql(configuration)
        self._cursor.execute(query, tuple(parameters))
        for row in self._cursor:
            return row[0] if type(row) == tuple else row['count']
        return 0

    def records(self, configuration, model):
        # I was going to get fancy and have this return an iterator, but since I'm going to load up
        # everything into a list anyway, I may as well just return the list, right?
        configuration = self._check_query_configuration(configuration)
        [query, parameters] = self.as_sql(configuration)
        self._cursor.execute(query, tuple(parameters))
        return [row for row in self._cursor]

    def as_sql(self, configuration):
        [wheres, parameters] = self._conditions_as_wheres_and_parameters(configuration['wheres'])
        select = configuration['selects'] if configuration['selects'] else '*'
        if configuration['joins']:
            joins = ' ' + ' '.join([join['raw'] for join in configuration['joins']])
        else:
            joins = ''
        if configuration['sorts']:
            order_by = ' ORDER BY ' + ', '.join(map(lambda sort: '`%s` %s' % (sort['column'], sort['direction']), configuration['sorts']))
        else:
            order_by = ''
        group_by = ' GROUP BY `' + configuration['group_by_column'] + '`' if configuration['group_by_column'] else ''
        limit = f' LIMIT {configuration["limit_start"]}, {configuration["limit_length"]}' if configuration['limit_length'] else ''
        return [
            f'SELECT {select} FROM `{configuration["table_name"]}`{joins}{wheres}{group_by}{order_by}{limit}'.strip(),
            parameters
        ]

    def as_count_sql(self, configuration):
        # note that this won't work if we start including a HAVING clause
        [wheres, parameters] = self._conditions_as_wheres_and_parameters(configuration['wheres'])
        # we also don't currently support parameters in the join clause - I'll probably need that though
        if configuration['joins']:
            # We can ignore left joins because they don't change the count
            join_sections = filter(lambda join: join['type'] != 'LEFT', configuration['joins'])
            joins = (' ' + ' '.join([join['raw'] for join in join_sections])) if join_sections else ''
        else:
            joins = ''
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
