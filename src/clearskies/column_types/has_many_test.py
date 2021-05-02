import unittest
from .has_many import HasMany
from ..models import Models
from ..model import Model
from .string import String
from .belongs_to import BelongsTo
from ..binding_specs import BindingSpec
from ..backends import MemoryBackend
from collections import OrderedDict


class User(Model):
    def __init__(self, memory_backend, columns):
        super().__init__(memory_backend, columns)

    def columns_configuration(self):
        return OrderedDict([
            ('status_id', {'class': BelongsTo, 'parent_models_class': Statuses}),
            ('first_name', {'class': String}),
            ('last_name', {'class': String}),
        ])

class Users(Models):
    def __init__(self, memory_backend, columns):
        super().__init__(memory_backend, columns)

    def model_class(self):
        return User

class Status(Model):
    def __init__(self, memory_backend, columns):
        super().__init__(memory_backend, columns)

    def columns_configuration(self):
        return OrderedDict([
            ('name', {'class': String}),
            ('users', {
                'class': HasMany,
                'child_models_class': Users,
                'readable_child_columns': ['first_name'],
                'is_readable': True,
            }),
        ])

class Statuses(Models):
    def __init__(self, memory_backend, columns):
        super().__init__(memory_backend, columns)

    def model_class(self):
        return Status

class HasManyTest(unittest.TestCase):
    def setUp(self):
        self.object_graph = BindingSpec.get_object_graph()
        self.memory_backend = self.object_graph.provide(MemoryBackend)
        self.users = self.object_graph.provide(Users)
        self.statuses = self.object_graph.provide(Statuses)
        self.has_many_users = self.statuses.columns()['users']
        self.memory_backend.create_table(self.users.empty_model())
        self.memory_backend.create_table(self.statuses.empty_model())
        self.pending = self.statuses.empty_model()
        self.pending.save({
            'name': 'pending',
        })
        self.approved = self.statuses.empty_model()
        self.approved.save({
            'name': 'approved',
        })

        self.john_pending = self.users.empty_model()
        self.john_pending.save({
            'status_id': self.pending.id,
            'first_name': 'John',
            'last_name': 'Doe',
        })
        self.jane_pending = self.users.empty_model()
        self.jane_pending.save({
            'status_id': self.pending.id,
            'first_name': 'Jane',
            'last_name': 'Doe',
        })
        self.janet_approved = self.users.empty_model()
        self.janet_approved.save({
            'status_id': self.approved.id,
            'first_name': 'Janet',
            'last_name': 'Doe',
        })

    def test_as_json(self):
        self.assertTrue(True)
        print(self.has_many_users.to_json(self.pending))
