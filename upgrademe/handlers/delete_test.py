import unittest
from .delete import Delete
from ..mocks import Models, Request
from ..column_types import String, Integer
from ..input_requirements import Required, MaximumLength
from ..authentication import Public, SecretBearer


class DeleteTest(unittest.TestCase):
    def setUp(self):
        Models.reset()
        self.models = Models({
            'name': {'class': String, 'input_requirements': [Required]},
            'email': {'class': String, 'input_requirements': [Required, (MaximumLength, 15)]},
            'age': {'class': Integer},
        })
        self.models.add_search_response([{'id': 5, 'name': 'Conor', 'email': 'c@example.com', 'age': 10}])

    def test_delete_flow(self):
        delete = Delete(
            Request(json={'id': '5'}),
            Public(),
            self.models
        )
        delete.configure({})
        response = delete()
        self.assertEquals('success', response[0]['status'])
        self.assertEquals(200, response[1])

        deleted = Models.deleted[0]
        self.assertEquals(5, deleted['id'])

        condition = Models.iterated[0]['conditions'][0]
        self.assertEquals('id', condition['column'])
        self.assertEquals(['5'], condition['values'])
        self.assertEquals('=', condition['operator'])

    #def test_input_checks(self):
        #update = Update(
            #Request(json={'id': 5, 'email': 'cmancone@example.com', 'age': 10}),
            #Public(),
            #self.models
        #)
        #update.configure({'columns': ['name', 'email', 'age']})
        #response = update()
        #self.assertEquals(200, response[1])
        #self.assertEquals(
            #{
                #'name': "'name' is required.",
                #'email': "'email' must be at most 15 characters long."
            #},
            #response[0]['inputErrors']
        #)

    #def test_columns(self):
        #self.models.add_update_response({
            #'id': 5,
            #'name': 'Conor',
            #'email': '',
            #'age': 10,
        #})

        #update = Update(
            #Request(json={'id': 5, 'name': 'Conor', 'age': 10}),
            #Public(),
            #self.models
        #)
        #update.configure({'columns': ['name', 'age']})
        #response = update()
        #response_data = response[0]['data']
        #self.assertEquals(200, response[1])
        #self.assertEquals(5, response_data['id'])
        #self.assertEquals(10, response_data['age'])
        #self.assertTrue('email' not in response_data)
        #self.assertEquals({'name': 'Conor', 'age': 10}, self.models.updated[0]['data'])

    #def test_extra_columns(self):
        #update = Update(
            #Request(json={'id': 5, 'name': 'Conor', 'age': 10, 'email': 'hey', 'yo': 'sup'}),
            #Public(),
            #self.models
        #)
        #update.configure({'columns': ['name', 'age']})
        #response = update()
        #self.assertEquals(
            #{
                #'email': "Input column 'email' is not an allowed column",
                #'yo': "Input column 'yo' is not an allowed column",
            #},
            #response[0]['inputErrors']
        #)

    #def test_readable_writeable(self):
        #self.models.add_update_response({
            #'id': 5,
            #'name': 'Conor',
            #'email': 'default@email.com',
            #'age': 10,
        #})

        #update = Update(
            #Request(json={'id': 5, 'name': 'Conor', 'age': 10}),
            #Public(),
            #self.models
        #)
        #update.configure({
            #'writeable_columns': ['name', 'age'],
            #'readable_columns': ['name', 'age', 'email'],
        #})
        #response = update()
        #response_data = response[0]['data']
        #self.assertEquals(200, response[1])
        #self.assertEquals(5, response_data['id'])
        #self.assertEquals(10, response_data['age'])
        #self.assertEquals('default@email.com', response_data['email'])
        #self.assertEquals({'name': 'Conor', 'age': 10}, self.models.updated[0]['data'])

    #def test_auth_failure(self):
        #update = Update(
            #Request(
                #json={'id': 5, 'name': 'Conor', 'email': 'c@example.com', 'age': 10},
                #headers={'Authorization': 'Bearer qwerty'},
            #),
            #SecretBearer('asdfer'),
            #self.models
        #)
        #update.configure({'columns': ['name', 'email', 'age']})
        #response = update()
        #self.assertEquals(401, response[1])
        #self.assertEquals('clientError', response[0]['status'])
        #self.assertEquals('Not Authorized', response[0]['error'])

    #def test_auth_success(self):
        #self.models.add_update_response({
            #'id': 5,
            #'name': 'Conor',
            #'email': 'default@email.com',
            #'age': 10,
        #})
        #update = Update(
            #Request(
                #json={'id': 5, 'name': 'Conor', 'email': 'c@example.com', 'age': 10},
                #headers={'Authorization': 'Bearer asdfer'},
            #),
            #SecretBearer('asdfer'),
            #self.models
        #)
        #update.configure({'columns': ['name', 'email', 'age']})
        #response = update()
        #self.assertEquals(200, response[1])

    #def test_require_id_column(self):
        #update = Update(
            #Request(
                #json={'name': 'Conor', 'email': 'c@example.com', 'age': 10},
                #headers={'Authorization': 'Bearer asdfer'},
            #),
            #SecretBearer('asdfer'),
            #self.models
        #)
        #update.configure({'columns': ['name', 'email', 'age']})
        #response = update()
        #self.assertEquals(404, response[1])
        #self.assertEquals("Missing 'id' in request body", response[0]['error'])

    #def test_require_matching_id(self):
        #self.models.clear_search_responses()
        #self.models.add_search_response([])
        #update = Update(
            #Request(
                #json={'id': 10, 'name': 'Conor', 'email': 'c@example.com', 'age': 10},
                #headers={'Authorization': 'Bearer asdfer'},
            #),
            #SecretBearer('asdfer'),
            #self.models
        #)
        #update.configure({'columns': ['name', 'email', 'age']})
        #response = update()
        #self.assertEquals(404, response[1])
        #self.assertEquals("Not Found", response[0]['error'])
