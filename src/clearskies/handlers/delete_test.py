import unittest
from .delete import Delete
from ..mocks import Models, InputOutput
from ..column_types import String, Integer
from ..input_requirements import Required, MaximumLength
from ..authentication import Public, SecretBearer
from clearskies.mocks import BindingSpec


class DeleteTest(unittest.TestCase):
    def setUp(self):
        Models.reset()
        self.models = Models({
            'name': {'class': String, 'input_requirements': [Required]},
            'email': {'class': String, 'input_requirements': [Required, (MaximumLength, 15)]},
            'age': {'class': Integer},
        })
        self.models.add_search_response([{'id': 5, 'name': 'Conor', 'email': 'c@example.com', 'age': 10}])
        self.object_graph = BindingSpec.get_object_graph()

    def test_delete_flow(self):
        delete = Delete(
            InputOutput(body={'id': '5'}),
            self.object_graph,
        )
        delete.configure({
            'models': self.models,
            'authentication': Public(),
        })
        response = delete()
        self.assertEquals('success', response[0]['status'])
        self.assertEquals(200, response[1])

        deleted = Models.deleted[0]
        self.assertEquals(5, deleted['id'])

        condition = Models.iterated[0]['wheres'][0]
        self.assertEquals('id', condition['column'])
        self.assertEquals(['5'], condition['values'])
        self.assertEquals('=', condition['operator'])
