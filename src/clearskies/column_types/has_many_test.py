import unittest
from .has_many import HasMany
from ..models import Models
from ..model import Model
from .string import String
from .belongs_to import BelongsTo
from ..backends import MemoryBackend
from collections import OrderedDict
from ..di import StandardDependencies


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
        self.di = StandardDependencies()
        self.memory_backend = self.di.build(MemoryBackend)
        self.users = self.di.build(Users)
        self.statuses = self.di.build(Statuses)
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
        self.assertEquals([
            OrderedDict([
                ('id', self.john_pending.id),
                ('first_name', self.john_pending.first_name),
            ]),
            OrderedDict([
                ('id', self.jane_pending.id),
                ('first_name', self.jane_pending.first_name),
            ]),
        ], self.has_many_users.to_json(self.pending))

    def test_auto_foreign_column(self):
        has_many = HasMany(self.di)
        has_many.configure('users', {'child_models_class': Users}, Status)
        self.assertEquals('status_id', has_many.config('foreign_column_name'))

    def test_require_child_model_class(self):
        has_many = HasMany(self.di)
        with self.assertRaises(KeyError) as context:
            has_many.configure('users', {}, str)
        self.assertIn("Missing required configuration 'child_models_class'", str(context.exception))

    def test_required_readable_columns_for_is_readable(self):
        has_many = HasMany(self.di)
        with self.assertRaises(ValueError) as context:
            has_many.configure(
                'users',
                {
                    'child_models_class': Users,
                    'is_readable': True,
                },
                Status,
            )
        self.assertIn("must provide 'readable_child_columns' if is_readable is set", str(context.exception))

    def test_readable_columns_iterable(self):
        has_many = HasMany(self.di)
        with self.assertRaises(ValueError) as context:
            has_many.configure(
                'users',
                {
                    'child_models_class': Users,
                    'is_readable': True,
                    'readable_child_columns': 5,
                },
                Status,
            )
        self.assertIn("'readable_child_columns' should be an iterable", str(context.exception))

    def test_readable_columns_invalid_column(self):
        has_many = HasMany(self.di)
        with self.assertRaises(ValueError) as context:
            has_many.configure(
                'users',
                {
                    'child_models_class': Users,
                    'is_readable': True,
                    'readable_child_columns': ['asdf'],
                },
                Status,
            )
        self.assertIn("readable_child_columns' references column named 'asdf' but", str(context.exception))
