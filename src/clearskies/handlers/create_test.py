import unittest
from .create import Create
from ..mocks import Models, InputOutput
from ..column_types import String, Integer
from ..input_requirements import Required, MaximumLength
from ..authentication import Public, SecretBearer


class CreateTest(unittest.TestCase):
    def setUp(self):
        Models.reset()
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
            InputOutput(body={'name': 'Conor', 'email': 'c@example.com', 'age': 10}),
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

    def test_input_checks(self):
        create = Create(
            InputOutput(body={'email': 'cmancone@example.com', 'age': 10}),
            Public(),
            self.models
        )
        create.configure({'columns': ['name', 'email', 'age']})
        response = create()
        self.assertEquals(200, response[1])
        self.assertEquals(
            {
                'name': "'name' is required.",
                'email': "'email' must be at most 15 characters long."
            },
            response[0]['inputErrors']
        )

    def test_columns(self):
        self.models.add_create_response({
            'id': 1,
            'name': 'Conor',
            'email': '',
            'age': 10,
        })

        create = Create(
            InputOutput(body={'name': 'Conor', 'age': 10}),
            Public(),
            self.models
        )
        create.configure({'columns': ['name', 'age']})
        response = create()
        response_data = response[0]['data']
        self.assertEquals(200, response[1])
        self.assertEquals(1, response_data['id'])
        self.assertEquals(10, response_data['age'])
        self.assertTrue('email' not in response_data)
        self.assertEquals({'name': 'Conor', 'age': 10}, Models.created[0]['data'])

    def test_extra_columns(self):
        create = Create(
            InputOutput(body={'name': 'Conor', 'age': 10, 'email': 'hey', 'yo': 'sup'}),
            Public(),
            self.models
        )
        create.configure({'columns': ['name', 'age']})
        response = create()
        self.assertEquals(
            {
                'email': "Input column 'email' is not an allowed column",
                'yo': "Input column 'yo' is not an allowed column",
            },
            response[0]['inputErrors']
        )

    def test_readable_writeable(self):
        self.models.add_create_response({
            'id': 1,
            'name': 'Conor',
            'email': 'default@email.com',
            'age': 10,
        })

        create = Create(
            InputOutput(body={'name': 'Conor', 'age': 10}),
            Public(),
            self.models
        )
        create.configure({
            'writeable_columns': ['name', 'age'],
            'readable_columns': ['name', 'age', 'email'],
        })
        response = create()
        response_data = response[0]['data']
        self.assertEquals(200, response[1])
        self.assertEquals(1, response_data['id'])
        self.assertEquals(10, response_data['age'])
        self.assertEquals('default@email.com', response_data['email'])
        self.assertEquals({'name': 'Conor', 'age': 10}, Models.created[0]['data'])

    def test_auth_failure(self):
        input_output = InputOutput(
            body={'name': 'Conor', 'email': 'c@example.com', 'age': 10},
            request_headers={'Authorization': 'Bearer qwerty'},
        )
        create = Create(input_output, SecretBearer(input_output, 'asdfer'), self.models)
        create.configure({'columns': ['name', 'email', 'age']})
        response = create()
        self.assertEquals(401, response[1])
        self.assertEquals('clientError', response[0]['status'])
        self.assertEquals('Not Authorized', response[0]['error'])

    def test_auth_success(self):
        self.models.add_create_response({
            'id': 1,
            'name': 'Conor',
            'email': 'default@email.com',
            'age': 10,
        })
        input_output = InputOutput(
            body={'name': 'Conor', 'email': 'c@example.com', 'age': 10},
            request_headers={'Authorization': 'Bearer asdfer'},
        )
        create = Create(input_output, SecretBearer(input_output, 'asdfer'),self.models)
        create.configure({'columns': ['name', 'email', 'age']})
        response = create()
        self.assertEquals(200, response[1])
