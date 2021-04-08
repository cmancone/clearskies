import unittest
from .memory_backend import MemoryBackend
from types import SimpleNamespace


class MemoryBackendTest(unittest.TestCase):
    def setUp(self):
        self.user_model = SimpleNamespace(table_name='users', columns_configuration=lambda: {'name': '', 'email': ''})
        self.reviews_model = SimpleNamespace(table_name='reviews', columns_configuration=lambda: {'review': ''})
        self.memory_backend = MemoryBackend()
        self.memory_backend.create_table(self.user_model)
        self.memory_backend.create_table(self.reviews_model)

    def test_create(self):
        self.memory_backend.create({'name': 'Conor', 'email': 'cmancone@example.com'}, self.user_model)
        self.memory_backend.create({'name': 'Ronoc', 'email': 'rmancone@example.com'}, self.user_model)
        self.memory_backend.iterator({'table_name': 'users'})
        self.assertEquals([
            {'id': 1, 'name': 'Conor', 'email': 'cmancone@example.com'},
            {'id': 2, 'name': 'Ronoc', 'email': 'rmancone@example.com'},
        ], self.memory_backend._iterator_rows)

    def test_create_check_columns(self):
        with self.assertRaises(ValueError) as context:
            self.memory_backend.create({'name': 'Conor', 'emails': 'cmancone@example.com'}, self.user_model)
        self.assertEquals(
            "Cannot create record: column 'emails' does not exist in table 'users'",
            str(context.exception)
        )

    def test_update(self):
        self.memory_backend.create({'name': 'Conor', 'email': 'cmancone@example.com'}, self.user_model)
        self.memory_backend.update(1, {'name': 'Ronoc', 'email': 'rmancone@example.com'}, self.user_model)
        self.memory_backend.iterator({'table_name': 'users'})
        self.assertEquals([
            {'id': 1, 'name': 'Ronoc', 'email': 'rmancone@example.com'},
        ], self.memory_backend._iterator_rows)

    def test_update_check_columns(self):
        self.memory_backend.create({'name': 'Conor', 'email': 'cmancone@example.com'}, self.user_model)
        with self.assertRaises(ValueError) as context:
            self.memory_backend.update(1, {'name': 'Conor', 'emails': 'cmancone@example.com'}, self.user_model)
        self.assertEquals(
            "Cannot update record: column 'emails' does not exist in table 'users'",
            str(context.exception)
        )
    def test_update_check_id(self):
        self.memory_backend.create({'name': 'Conor', 'email': 'cmancone@example.com'}, self.user_model)
        with self.assertRaises(ValueError) as context:
            self.memory_backend.update(2, {'name': 'Conor', 'emails': 'cmancone@example.com'}, self.user_model)
        self.assertEquals(
            "Cannot update non existent record with id of '2'",
            str(context.exception)
        )

    def test_delete(self):
        self.memory_backend.create({'name': 'Conor', 'email': 'cmancone@example.com'}, self.user_model)
        self.memory_backend.delete(1, self.user_model)
        self.memory_backend.iterator({'table_name': 'users'})
        self.assertEquals([], self.memory_backend._iterator_rows)
        self.assertEquals(0, len(self.memory_backend._iterator_rows))

    def test_multiple_tables(self):
        self.memory_backend.create({'name': 'Conor', 'email': 'cmancone@example.com'}, self.user_model)
        self.memory_backend.create({'review': 'cool'}, self.reviews_model)
        self.memory_backend.create({'review': 'bad'}, self.reviews_model)
        self.memory_backend.update(2, {'review': 'okay'}, self.reviews_model)
        self.memory_backend.iterator({'table_name': 'reviews'})
        self.assertEquals([
            {'id': 1, 'review': 'cool'},
            {'id': 2, 'review': 'okay'},
        ], self.memory_backend._iterator_rows)
        self.memory_backend.iterator({'table_name': 'users'})
        self.assertEquals([
            {'id': 1, 'name': 'Conor', 'email': 'cmancone@example.com'},
        ], self.memory_backend._iterator_rows)

    def test_filter_and_sort(self):
        self.memory_backend.create({'name': 'Zeb', 'email': 'a@example.com'}, self.user_model)
        self.memory_backend.create({'name': 'Zeb', 'email': 'b@example.com'}, self.user_model)
        self.memory_backend.create({'name': 'A', 'email': 'c@example.com'}, self.user_model)
        self.memory_backend.iterator({
            'table_name': 'users',
            'wheres': [{'column': 'name', 'operator': '=', 'values': ['Zeb']}],
            'sorts': [
                {'column': 'email', 'direction': 'DESC'},
            ]
        })
        self.assertEquals([
            {'id': 2, 'name': 'Zeb', 'email': 'b@example.com'},
            {'id': 1, 'name': 'Zeb', 'email': 'a@example.com'},
        ], self.memory_backend._iterator_rows)

        self.memory_backend.iterator({
            'table_name': 'users',
            'wheres': [{'column': 'id', 'operator': 'in', 'values': [2, 3]}],
            'sorts': [
                {'column': 'name', 'direction': 'ASC'},
            ]
        })
        self.assertEquals([
            {'id': 3, 'name': 'A', 'email': 'c@example.com'},
            {'id': 2, 'name': 'Zeb', 'email': 'b@example.com'},
        ], self.memory_backend._iterator_rows)

        self.memory_backend.iterator({
            'table_name': 'users',
            'wheres': [
                {'column': 'name', 'operator': '=', 'values': ['Zeb']},
                {'column': 'email', 'operator': 'like', 'values': ['a@example.com']}
            ],
        })
        self.assertEquals([
            {'id': 1, 'name': 'Zeb', 'email': 'a@example.com'},
        ], self.memory_backend._iterator_rows)

        self.memory_backend.iterator({
            'table_name': 'users',
            'sorts': [
                {'column': 'name', 'direction': 'ASC'},
                {'column': 'email', 'direction': 'DESC'},
            ],
        })
        self.assertEquals([
            {'id': 3, 'name': 'A', 'email': 'c@example.com'},
            {'id': 2, 'name': 'Zeb', 'email': 'b@example.com'},
            {'id': 1, 'name': 'Zeb', 'email': 'a@example.com'},
        ], self.memory_backend._iterator_rows)

        self.memory_backend.iterator({
            'table_name': 'users',
            'sorts': [
                {'column': 'name', 'direction': 'ASC'},
                {'column': 'email', 'direction': 'DESC'},
            ],
            'limit_start': 1,
            'limit_length': 1,
        })
        self.assertEquals([
            {'id': 2, 'name': 'Zeb', 'email': 'b@example.com'},
        ], self.memory_backend._iterator_rows)

    def test_count(self):
        self.memory_backend.create({'name': 'Zeb', 'email': 'a@example.com'}, self.user_model)
        self.memory_backend.create({'name': 'Zeb', 'email': 'b@example.com'}, self.user_model)
        self.memory_backend.create({'name': 'A', 'email': 'c@example.com'}, self.user_model)
        self.assertEquals(
            2,
            self.memory_backend.count({
                'table_name': 'users',
                'wheres': [{'column': 'name', 'operator': '=', 'values': ['Zeb']}],
                'sorts': [
                    {'column': 'email', 'direction': 'DESC'},
                ],
                'limit_length': 1
            })
        )
