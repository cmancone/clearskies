import unittest
from collections import OrderedDict
from ....model import Model
from ....models import Models
from ....column_types import string, integer
from ....handlers import SimpleRouting, RestfulAPI
from ....authentication import secret_bearer
from ....di import StandardDependencies
from ....backends import MemoryBackend
from .oai3_json import OAI3JSON
import os
class User(Model):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

    def columns_configuration(self):
        return OrderedDict([
            string('name'),
            integer('age'),
        ])
class Status(Model):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

    def columns_configuration(self):
        return OrderedDict([
            string('name'),
            integer('order'),
        ])
class SimpleRoutingTest(unittest.TestCase):
    def setUp(self):
        self.di = StandardDependencies()
        self.memory_backend = MemoryBackend()
        self.di.bind('cursor_backend', self.memory_backend)
        self.handler = SimpleRouting(self.di)
        self.handler.configure({
            'authentication':
            secret_bearer(secret='asdfer'),
            'routes': [{
                'path': '/users/',
                'handler_class': RestfulAPI,
                'handler_config': {
                    'model_class': User,
                    'readable_columns': ['name', 'age'],
                    'writeable_columns': ['name', 'age'],
                    'searchable_columns': ['name'],
                    'sortable_columns': ['name', 'age'],
                    'default_sort_column': 'name',
                },
            }, {
                'path': '/statuses/',
                'handler_class': RestfulAPI,
                'handler_config': {
                    'read_only': True,
                    'model_class': Status,
                    'readable_columns': ['name'],
                    'searchable_columns': ['name'],
                    'sortable_columns': ['name'],
                    'default_sort_column': 'name',
                },
            }, {
                'path': '/v1/',
                'handler_class': SimpleRouting,
                'handler_config': {
                    'routes': [
                        {
                            'path': 'statuses',
                            'handler_class': RestfulAPI,
                            'handler_config': {
                                'read_only': True,
                                'model_class': Status,
                                'readable_columns': ['name'],
                                'searchable_columns': ['name'],
                                'sortable_columns': ['name'],
                                'default_sort_column': 'name',
                            },
                        },
                    ]
                }
            }],
        })

    def test_full_json_conversion(self):
        oai3_json = self.di.build(OAI3JSON)
        oai3_json.set_requests(self.handler.documentation())
        oai3_json.set_components(self.handler.documentation_components())
        doc = oai3_json.pretty(
            root_properties={
                "info": {
                    "title": "Auto generated by clearskies",
                    "version": "1.0"
                },
                "servers": [
                    {
                        "url": "https://production.example.com/v1",
                        "description": "Production"
                    },
                ]
            }
        )

        with open(os.path.dirname(__file__) + '/test.json') as test_file:
            desired_contents = test_file.read().strip()

        self.assertEquals(desired_contents, doc)
