import unittest
from .create import Create
from ..mocks import Models, Request
from ..column_types import String, Integer
from ..input_requirements import Required, MaximumLength
from ..authentication import Public


class CreateTest(unittest.TestCase):
    def setUp(self):
        self.models = Models({
            'name': {'class': String, 'input_requirements': [Required]},
            'email': {'class': String, 'input_requirements': [Required, (MaximumLength, 15)]},
            'age': {'class': Integer},
        })

    def test_save_flow(self):
        self.models.add_create_response({
            'id': 1,
            'name': 'Conor',
            'email': 'c@example.com',
            'age': 10,
        })

        create = Create(
            Request(json={'name': 'Conor', 'email': 'c@example.com', 'age': 10}),
            Public(),
            self.models
        )
        create.configure({'columns': ['name', 'email', 'age']})
        response = create()
        response_data = response[0]['data']
        self.assertEquals(200, response[1])
        self.assertEquals(1, response_data['id'])
        self.assertEquals(10, response_data['age'])
        self.assertEquals('Conor', response_data['name'])
        self.assertEquals('c@example.com', response_data['email'])
