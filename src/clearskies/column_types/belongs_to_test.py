import unittest
from unittest.mock import MagicMock, call
from .belongs_to import BelongsTo
from ..mocks.models import Models
from .string import String


class BelongsToTest(unittest.TestCase):
    def setUp(self):
        Models.reset()
        self.models = Models({
            'name': {'class': String},
        })

        self.object_graph = type('', (), {'provide': MagicMock(return_value=self.models)})()
        self.belongs_to = BelongsTo(self.object_graph)

    def test_configure(self):
        self.belongs_to.configure('user_id', {'parent_models_class': Models}, BelongsToTest)
        self.object_graph.provide.assert_called_with(Models)

    def test_require_proper_name(self):
        with self.assertRaises(ValueError) as context:
            self.belongs_to.configure('user', {'parent_models_class': Models}, BelongsToTest)
        self.assertEquals(
            "Invalid name for column 'user' in 'BelongsToTest' - BelongsTo column names must end in '_id'",
            str(context.exception)
        )

    def test_require_parent_models_class(self):
        with self.assertRaises(KeyError) as context:
            self.belongs_to.configure('user_id', {}, BelongsToTest)
        self.assertEquals(
            "\"Missing required configuration 'parent_models_class' for column 'user_id' in 'BelongsToTest'\"",
            str(context.exception)
        )

    def test_check_input_no_match(self):
        self.models.add_search_response([])
        self.belongs_to.configure('user_id', {'parent_models_class': Models}, BelongsToTest)
        error = self.belongs_to.input_errors('model', {'user_id': 5})
        self.assertEquals({'user_id': 'Invalid selection for user_id: record does not exist'}, error)
        self.assertEquals(1, len(Models.counted))
        self.assertEquals(
            [{'column': 'user_id', 'operator': '=', 'values': ['5'], 'parsed': 'user_id=?'}],
            Models.counted[0]['wheres']
        )

    def test_check_input_match(self):
        self.models.add_search_response([{'id': 1}])
        self.belongs_to.configure('user_id', {'parent_models_class': Models}, BelongsToTest)
        error = self.belongs_to.input_errors('model', {'user_id': 10})
        self.assertEquals({}, error)
        self.assertEquals(1, len(Models.counted))
        self.assertEquals(
            [{'column': 'user_id', 'operator': '=', 'values': ['10'], 'parsed': 'user_id=?'}],
            Models.counted[0]['wheres']
        )

    def test_check_input_null(self):
        self.models.add_search_response([{'id': 1}])
        self.belongs_to.configure('user_id', {'parent_models_class': Models}, BelongsToTest)
        error = self.belongs_to.input_errors('model', {'user_id': None})
        self.assertEquals({}, error)
        self.assertEquals(None, Models.counted)

    def test_provide(self):
        self.models.add_search_response([{'id': 2, 'name': 'hey'}])
        self.belongs_to.configure('user_id', {'parent_models_class': Models}, BelongsToTest)
        self.assertTrue(self.belongs_to.can_provide('user'))
        self.assertFalse(self.belongs_to.can_provide('users'))

        user = self.belongs_to.provide({'user_id': 2}, 'user_id')
        self.assertEquals(2, user.id)
        self.assertEquals('hey', user.name)
        self.assertEquals(1, len(Models.iterated))
        self.assertEquals(
            [{'column': 'user_id', 'operator': '=', 'values': ['2'], 'parsed': 'user_id=?'}],
            Models.iterated[0]['wheres']
        )
