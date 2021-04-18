import unittest
from .update import Update
from ..mocks import Models, InputOutput
from ..column_types import String, Integer
from ..input_requirements import Required, MaximumLength
from ..authentication import Public, SecretBearer
from clearskies.mocks import BindingSpec


class UpdateTest(unittest.TestCase):
    def setUp(self):
        Models.reset()
        self.models = Models({
            'name': {'class': String, 'input_requirements': [Required]},
            'email': {'class': String, 'input_requirements': [Required, (MaximumLength, 15)]},
            'age': {'class': Integer},
        })
        self.models.add_search_response([{'id': 5, 'name': '', 'email': '', 'age': 0}])
        self.object_graph = BindingSpec.get_object_graph()

    def test_save_flow(self):
        self.models.add_update_response({
            'id': 5,
            'name': 'Conor',
            'email': 'c@example.com',
            'age': 10,
        })

        update = Update(
            InputOutput(body={'id': '5', 'name': 'Conor', 'email': 'c@example.com', 'age': 10}),
            self.object_graph,
        )
        update.configure({
            'models': self.models,
            'columns': ['name', 'email', 'age'],
            'authentication': Public(),
        })
        response = update()
        response_data = response[0]['data']
        self.assertEquals(200, response[1])
        self.assertEquals(5, response_data['id'])
        self.assertEquals(10, response_data['age'])
        self.assertEquals('Conor', response_data['name'])
        self.assertEquals('c@example.com', response_data['email'])

        update = Models.updated[0]
        self.assertEquals(5, update['id'])
        self.assertEquals({'name': 'Conor', 'email': 'c@example.com', 'age': 10}, update['data'])

        condition = Models.iterated[0]['wheres'][0]
        self.assertEquals('id', condition['column'])
        self.assertEquals(['5'], condition['values'])
        self.assertEquals('=', condition['operator'])

    def test_input_checks(self):
        update = Update(
            InputOutput(body={'id': 5, 'email': 'cmancone@example.com', 'age': 10}),
            self.object_graph
        )
        update.configure({
            'models': self.models,
            'columns': ['name', 'email', 'age'],
            'authentication': Public(),
        })
        response = update()
        self.assertEquals(200, response[1])
        self.assertEquals(
            {
                'name': "'name' is required.",
                'email': "'email' must be at most 15 characters long."
            },
            response[0]['inputErrors']
        )

    def test_columns(self):
        self.models.add_update_response({
            'id': 5,
            'name': 'Conor',
            'email': '',
            'age': 10,
        })

        update = Update(
            InputOutput(body={'id': 5, 'name': 'Conor', 'age': 10}),
            self.object_graph
        )
        update.configure({
            'models': self.models,
            'columns': ['name', 'age'],
            'authentication': Public(),
        })
        response = update()
        response_data = response[0]['data']
        self.assertEquals(200, response[1])
        self.assertEquals(5, response_data['id'])
        self.assertEquals(10, response_data['age'])
        self.assertTrue('email' not in response_data)
        self.assertEquals({'name': 'Conor', 'age': 10}, self.models.updated[0]['data'])

    def test_extra_columns(self):
        update = Update(
            InputOutput(body={'id': 5, 'name': 'Conor', 'age': 10, 'email': 'hey', 'yo': 'sup'}),
            self.object_graph
        )
        update.configure({
            'models': self.models,
            'columns': ['name', 'age'],
            'authentication': Public(),
        })
        response = update()
        self.assertEquals(
            {
                'email': "Input column 'email' is not an allowed column",
                'yo': "Input column 'yo' is not an allowed column",
            },
            response[0]['inputErrors']
        )

    def test_readable_writeable(self):
        self.models.add_update_response({
            'id': 5,
            'name': 'Conor',
            'email': 'default@email.com',
            'age': 10,
        })

        update = Update(
            InputOutput(body={'id': 5, 'name': 'Conor', 'age': 10}),
            self.object_graph,
        )
        update.configure({
            'models': self.models,
            'writeable_columns': ['name', 'age'],
            'readable_columns': ['name', 'age', 'email'],
            'authentication': Public(),
        })
        response = update()
        response_data = response[0]['data']
        self.assertEquals(200, response[1])
        self.assertEquals(5, response_data['id'])
        self.assertEquals(10, response_data['age'])
        self.assertEquals('default@email.com', response_data['email'])
        self.assertEquals({'name': 'Conor', 'age': 10}, self.models.updated[0]['data'])

    def test_auth_failure(self):
        input_output = InputOutput(
            body={'id': 5, 'name': 'Conor', 'email': 'c@example.com', 'age': 10},
            request_headers={'Authorization': 'Bearer qwerty'},
        )
        secret_bearer = SecretBearer(input_output, 'environment')
        secret_bearer.configure(secret='asdfer')
        update = Update(input_output, self.object_graph)
        update.configure({
            'models': self.models,
            'columns': ['name', 'email', 'age'],
            'authentication': secret_bearer,
        })
        response = update()
        self.assertEquals(401, response[1])
        self.assertEquals('clientError', response[0]['status'])
        self.assertEquals('Not Authenticated', response[0]['error'])

    def test_auth_success(self):
        self.models.add_update_response({
            'id': 5,
            'name': 'Conor',
            'email': 'default@email.com',
            'age': 10,
        })
        input_output = InputOutput(
            body={'id': 5, 'name': 'Conor', 'email': 'c@example.com', 'age': 10},
            request_headers={'Authorization': 'Bearer asdfer'},
        )
        secret_bearer = SecretBearer(input_output, 'environment')
        secret_bearer.configure(secret='asdfer')
        update = Update(input_output, self.object_graph)
        update.configure({
            'models': self.models,
            'columns': ['name', 'email', 'age'],
            'authentication': secret_bearer,
        })
        response = update()
        self.assertEquals(200, response[1])

    def test_require_id_column(self):
        update = Update(
            InputOutput(
                body={'name': 'Conor', 'email': 'c@example.com', 'age': 10},
            ),
            self.object_graph
        )
        update.configure({
            'models': self.models,
            'columns': ['name', 'email', 'age'],
            'authentication': Public(),
        })
        response = update()
        self.assertEquals(404, response[1])
        self.assertEquals("Missing 'id' in request body", response[0]['error'])

    def test_require_matching_id(self):
        self.models.clear_search_responses()
        self.models.add_search_response([])
        update = Update(
            InputOutput(
                body={'id': 10, 'name': 'Conor', 'email': 'c@example.com', 'age': 10},
            ),
            self.object_graph
        )
        update.configure({
            'models': self.models,
            'columns': ['name', 'email', 'age'],
            'authentication': Public(),
        })
        response = update()
        self.assertEquals(404, response[1])
        self.assertEquals("Not Found", response[0]['error'])
