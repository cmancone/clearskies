from collections import OrderedDict
from clearskies import Model
from clearskies.column_types import belongs_to, email, string, integer, created, updated
from clearskies.input_requirements import required, maximum_length
from . import statuses


class User(Model):
    def __init__(self, cursor_backend, columns):
        super().__init__(cursor_backend, columns)

    def columns_configuration(self):
        return OrderedDict([
            belongs_to('status_id', parent_models_class=statuses.Statuses, input_requirements=[required()]),
            string('name', input_requirements=[required(), maximum_length(255)]),
            email('email', input_requirements=[required(), maximum_length(255)]),
            created('created'),
            updated('updated'),
        ])
