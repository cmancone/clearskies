import unittest
from unittest.mock import MagicMock, call
from .cursor_backend import CursorBackend
from collections import OrderedDict


class CursorBackendTest(unittest.TestCase):
    def setUp(self):
        self.model = type('', (), {'table_name': 'my_table'})
        self.cursor = type('', (), {
            'execute': MagicMock(),
            'next': MagicMock(return_value={'my': 'data'}),
            'lastrowid': 10,
        })()
        self.backend = CursorBackend(self.cursor)

    def test_create(self):
        new_data = self.backend.create({'dummy': 'data', 'hey': 'people'}, self.model)
        self.cursor.execute.assert_has_calls([
            call('INSERT INTO `my_table` (`dummy`, `hey`) VALUES (?, ?)', ['data', 'people']),
            call('SELECT * FROM `my_table` WHERE id=?', [10]),
        ])
        self.assertEquals({'my': 'data'}, new_data)

    def test_update(self):
        to_save = OrderedDict([('hey', 'sup'), ('qwerty', 'asdf'), ('foo', 'bar')])
        new_data = self.backend.update(5, to_save, self.model)
        self.cursor.execute.assert_has_calls([
            call('UPDATE `my_table` SET `hey`=?, `qwerty`=?, `foo`=? WHERE id=?', ['sup', 'asdf', 'bar', 5]),
            call('SELECT * FROM `my_table` WHERE id=?', [5]),
        ])
        self.assertEquals({'my': 'data'}, new_data)
