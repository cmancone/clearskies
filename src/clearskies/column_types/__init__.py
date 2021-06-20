from .belongs_to import BelongsTo
from .column import Column
from .created import Created
from .datetime import DateTime
from .email import Email
from .float import Float
from .has_many import HasMany
from .integer import Integer
from .json import JSON
from .many_to_many import ManyToMany
from .string import String
from .updated import Updated

def build_column_config(name, column_class, **kwargs):
    return (
        name,
        {
            **{"class": column_class},
            **kwargs
        }
    )

def belongs_to(name, **kwargs):
    return build_column_config(name, BelongsTo, **kwargs)

def created(name, **kwargs):
    return build_column_config(name, Created, **kwargs)

def datetime(name, **kwargs):
    return build_column_config(name, DateTime, **kwargs)

def email(name, **kwargs):
    return build_column_config(name, Email, **kwargs)

def float_column(name, **kwargs):
    return build_column_config(name, Float, **kwargs)

def has_many(name, **kwargs):
    return build_column_config(name, HasMany, **kwargs)

def integer(name, **kwargs):
    return build_column_config(name, Integer, **kwargs)

def json(name, **kwargs):
    return build_column_config(name, JSON, **kwargs)

def many_to_many(name, **kwargs):
    return build_column_config(name, ManyToMany, **kwargs)

def string(name, **kwargs):
    return build_column_config(name, String, **kwargs)

def updated(name, **kwargs):
    return build_column_config(name, Updated, **kwargs)
