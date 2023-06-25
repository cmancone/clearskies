from .merge import merge
from typing import Dict


def schema(schema, writeable_columns=None):
    def wrap_in_application(function):
        return merge(function, schema=schema, writeable_columns=writeable_columns)

    wrap_in_application.is_wrapped_application = True
    return wrap_in_application
