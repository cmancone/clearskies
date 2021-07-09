from collections import OrderedDict
from clearskies import Model
from clearskies.column_types import string, has_many
from clearskies.input_requirements import required, maximum_length
from . import users


class Status(Model):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

    def columns_configuration(self):
        return OrderedDict([
            string('name'),
            has_many(
                'users',
                child_models_class=users.Users,
                is_readable=True,
                readable_child_columns=['status_id', 'name', 'email'],
            ),
        ])
