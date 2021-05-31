import unittest
from unittest.mock import MagicMock, call
from .restful_api import RestfulAPI
from ..mocks import InputOutput, Models
from ..authentication import Public
from ..column_types import String
from collections import OrderedDict
from ..di import StandardDependencies


class RestfulAPITest(unittest.TestCase):
    models = None

    def setUp(self):
        Models.reset()
        self.models = Models({
            'name': {'class': String},
        })
        self.di = StandardDependencies()

    def build_api(self, *args, **kwargs):
        input_output = InputOutput(*args, **kwargs)
        di = StandardDependencies(bindings={
            'input_output': input_output,
            'models': self.models,
        })
        return [di.build(RestfulAPI), input_output]

    def test_get_record(self):
        self.models.add_search_response([{'id': '134', 'name': 'sup'}])
        self.models.add_search_response([{'id': '134', 'name': 'sup'}])
        [api, input_output] = self.build_api(path_info='/134')
        api.configure({
            'models': self.models,
            'readable_columns': ['name'],
            'writeable_columns': ['name'],
            'searchable_columns': ['name'],
            'sortable_columns': ['name'],
            'default_sort_column': 'name',
            'where': ['age=5'],
            'authentication': Public(),
        })
        result = api(input_output)
        self.assertEquals(200, result[1])
        self.assertEquals(OrderedDict([('id', 134), ('name', 'sup')]), result[0]['data'])
        self.assertEquals({}, result[0]['pagination'])


    def test_get_records(self):
        self.models.add_search_response([{'id': '134', 'name': 'sup'}, {'id': '234', 'name': 'hey'}])
        self.models.add_search_response([{'id': '134', 'name': 'sup'}, {'id': '234', 'name': 'hey'}])
        [api, input_output] = self.build_api()
        api.configure({
            'models': self.models,
            'readable_columns': ['name'],
            'writeable_columns': ['name'],
            'searchable_columns': ['name'],
            'sortable_columns': ['name'],
            'default_sort_column': 'name',
            'authentication': Public(),
        })
        result = api(input_output)
        self.assertEquals(200, result[1])
        self.assertEquals(OrderedDict([('id', 134), ('name', 'sup')]), result[0]['data'][0])
        self.assertEquals(OrderedDict([('id', 234), ('name', 'hey')]), result[0]['data'][1])
        self.assertEquals({'numberResults': 2, 'start': 0, 'limit': 100}, result[0]['pagination'])

    def test_create_record(self):
        self.models.add_create_response({'id': 1, 'name': 'Conor'})
        [api, input_output] = self.build_api(request_method='POST', body={'name': 'Conor'})
        api.configure({
            'models': self.models,
            'readable_columns': ['name'],
            'writeable_columns': ['name'],
            'searchable_columns': ['name'],
            'sortable_columns': ['name'],
            'default_sort_column': 'name',
            'authentication': Public(),
        })
        result = api(input_output)
        self.assertEquals(200, result[1])
        self.assertEquals(OrderedDict([('id', 1), ('name', 'Conor')]), result[0]['data'])
        self.assertEquals({}, result[0]['pagination'])
        self.assertEquals({'name': 'Conor'}, Models.created[0]['data'])

    def test_update_record(self):
        self.models.add_search_response([{'id': 125, 'name': 'Ronoc'}])
        self.models.add_update_response({'id': 125, 'name': 'Conor'})
        [api, input_output] = self.build_api(
            request_method='PUT',
            path_info='/125',
            body={'name': 'Conor'},
        )
        api.configure({
            'models': self.models,
            'readable_columns': ['name'],
            'writeable_columns': ['name'],
            'searchable_columns': ['name'],
            'sortable_columns': ['name'],
            'default_sort_column': 'name',
            'authentication': Public(),
        })
        result = api(input_output)
        self.assertEquals(200, result[1])
        self.assertEquals(OrderedDict([('id', 125), ('name', 'Conor')]), result[0]['data'])
        self.assertEquals({}, result[0]['pagination'])
        self.assertEquals(125, Models.updated[0]['id'])
        self.assertEquals({'name': 'Conor'}, Models.updated[0]['data'])
        self.assertEquals([
            {'column': 'id', 'operator': '=', 'values': ['125'], 'parsed': 'id=?'},
        ], Models.iterated[0]['wheres'])

    def test_delete_record(self):
        self.models.add_search_response([{'id': 125, 'name': 'Ronoc'}])
        [api, input_output] = self.build_api(
            request_method='DELETE',
            path_info='/125',
        )
        api.configure({
            'models': self.models,
            'readable_columns': ['name'],
            'writeable_columns': ['name'],
            'searchable_columns': ['name'],
            'sortable_columns': ['name'],
            'default_sort_column': 'name',
            'authentication': Public(),
        })
        result = api(input_output)
        self.assertEquals(200, result[1])
        self.assertEquals({}, result[0]['data'])
        self.assertEquals({}, result[0]['pagination'])
        self.assertEquals(125, Models.deleted[0]['id'])
        self.assertEquals([
            {'column': 'id', 'operator': '=', 'values': ['125'], 'parsed': 'id=?'},
        ], Models.iterated[0]['wheres'])

    def test_search(self):
        self.models.add_search_response([{'id': '134', 'name': 'sup'}, {'id': '234', 'name': 'hey'}])
        self.models.add_search_response([{'id': '134', 'name': 'sup'}, {'id': '234', 'name': 'hey'}])
        [api, input_output] = self.build_api(
            path_info='/search',
            body={'where': [{'column': 'name', 'value': 'hey'}]}
        )
        api.configure({
            'models': self.models,
            'readable_columns': ['name'],
            'writeable_columns': ['name'],
            'searchable_columns': ['name'],
            'sortable_columns': ['name'],
            'default_sort_column': 'name',
            'authentication': Public(),
        })
        result = api(input_output)
        self.assertEquals(200, result[1])
        self.assertEquals(OrderedDict([('id', 134), ('name', 'sup')]), result[0]['data'][0])
        self.assertEquals(OrderedDict([('id', 234), ('name', 'hey')]), result[0]['data'][1])
        self.assertEquals({'numberResults': 2, 'start': 0, 'limit': 100}, result[0]['pagination'])
        self.assertEquals(
            [{'column': 'name', 'operator': 'LIKE', 'values': ['%hey%'], 'parsed': 'name LIKE ?'}],
            Models.iterated[0]['wheres']
        )
