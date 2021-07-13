import unittest
from unittest.mock import MagicMock, call
from .cursor_backend import CursorBackend
from collections import OrderedDict, namedtuple


class CursorBackendTest(unittest.TestCase):
    def setUp(self):
        self.model = type('', (), {'table_name': 'my_table'})
        self.cursor = type('', (), {
            'execute': MagicMock(),
            'lastrowid': 10,
            '__iter__': lambda x: iter([{'my': 'data'}]),
        })()
        self.backend = CursorBackend(self.cursor)

    def test_create(self):
        new_data = self.backend.create({'dummy': 'data', 'hey': 'people'}, self.model)
        self.cursor.execute.assert_has_calls([
            call('INSERT INTO `my_table` (`dummy`, `hey`) VALUES (%s, %s)', ('data', 'people')),
            call('SELECT * FROM `my_table` WHERE id=%s', (10,)),
        ])
        self.assertEquals({'my': 'data'}, new_data)

    def test_update(self):
        to_save = OrderedDict([('hey', 'sup'), ('qwerty', 'asdf'), ('foo', 'bar')])
        new_data = self.backend.update(5, to_save, self.model)
        self.cursor.execute.assert_has_calls([
            call('UPDATE `my_table` SET `hey`=%s, `qwerty`=%s, `foo`=%s WHERE id=%s', ('sup', 'asdf', 'bar', 5)),
            call('SELECT * FROM `my_table` WHERE id=%s', (5,)),
        ])
        self.assertEquals({'my': 'data'}, new_data)

    def test_delete(self):
        status = self.backend.delete(5, self.model)
        self.cursor.execute.assert_has_calls([
            call('DELETE FROM `my_table` WHERE id=%s', (5,)),
        ])
        self.assertEquals(True, status)

    def test_count_group(self):
        self.cursor = type('', (), {
            'execute': MagicMock(),
            'lastrowid': 10,
            '__iter__': lambda x: iter([{'count': 10}]),
        })()
        self.backend = CursorBackend(self.cursor)

        my_count = self.backend.count({
            'table_name': 'my_table',
            'group_by_column': 'age',
            'limit_start': 5,
            'limit_length': 10,
            'sorts': [{'column': 'name', 'direction': 'asc'}],
            'joins': [
                {
                    'type': 'LEFT',
                    'raw': 'LEFT JOIN dogs ON dogs.id=ages.id',
                },
                {
                    'type': 'INNER',
                    'raw': 'JOIN peeps AS peeps ON peeps.id=dogs.id',
                },
            ],
            'selects': 'sup',
            'wheres': [
                {'values': [5], 'parsed': 'id=%s'},
                {'values': ['2', '3'], 'parsed': 'status_id IN (%s,%s)'},
            ],
        }, 'model')
        self.assertEquals(10, my_count)
        self.cursor.execute.assert_called_with(
            'SELECT COUNT(' + \
                'SELECT 1 FROM `my_table` JOIN peeps AS peeps ON peeps.id=dogs.id ' + \
                'WHERE id=%s AND status_id IN (%s,%s) ' + \
                'GROUP BY `age`' + \
            ') AS count',
            (5, '2', '3')
        )

    def test_count(self):
        self.cursor = type('', (), {
            'execute': MagicMock(),
            'lastrowid': 10,
            '__iter__': lambda x: iter([{'count': 10}]),
        })()
        self.backend = CursorBackend(self.cursor)

        my_count = self.backend.count({
            'table_name': 'my_table',
            'limit_start': 5,
            'limit_length': 10,
            'sorts': [{'column': 'name', 'direction': 'asc'}],
            'joins': [
                {
                    'type': 'LEFT',
                    'raw': 'LEFT JOIN dogs ON dogs.id=ages.id',
                },
                {
                    'type': 'INNER',
                    'raw': 'JOIN peeps AS peeps ON peeps.id=dogs.id'
                },
            ],
            'selects': 'sup',
            'wheres': [
                {'values': [5], 'parsed': 'id=%s'},
                {'values': ['2', '3'], 'parsed': 'status_id IN (%s,%s)'},
            ],
        }, 'model')
        self.assertEquals(10, my_count)
        self.cursor.execute.assert_called_with(
            'SELECT COUNT(*) AS count FROM `my_table` JOIN peeps AS peeps ON peeps.id=dogs.id ' + \
                'WHERE id=%s AND status_id IN (%s,%s)',
            (5, '2', '3')
        )

    def test_iterate(self):
        results = self.backend.records({
            'table_name': 'my_table',
            'limit_start': 5,
            'limit_length': 10,
            'group_by_column': 'age',
            'sorts': [{'column': 'name', 'direction': 'ASC'}, {'column': 'first', 'direction': 'DESC'}],
            'joins': [{'raw': 'LEFT JOIN dogs ON dogs.id=ages.id'}, {'raw': 'JOIN peeps AS peeps ON peeps.id=dogs.id'}],
            'selects': 'sup',
            'wheres': [
                {'values': [5], 'parsed': 'id=%s'},
                {'values': ['2', '3'], 'parsed': 'status_id IN (%s,%s)'},
            ],
        }, 'model')
        self.cursor.execute.assert_called_with(
            'SELECT sup FROM `my_table` ' +
                'LEFT JOIN dogs ON dogs.id=ages.id ' + \
                'JOIN peeps AS peeps ON peeps.id=dogs.id ' + \
                'WHERE id=%s AND status_id IN (%s,%s) ' + \
                'GROUP BY `age` ' + \
                'ORDER BY `name` ASC, `first` DESC ' + \
                'LIMIT 5, 10',
            (5, '2', '3')
        )
        self.assertEquals([{'my': 'data'}], results)
