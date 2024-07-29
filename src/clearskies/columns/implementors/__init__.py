from .audit import Audit
from .belongs_to import BelongsTo
from .boolean import Boolean
from .category_tree import CategoryTree
from .column import Column
from .created import Created
from .created_by_authorization_data import CreatedByAuthorizationData
from .created_by_header import CreatedByHeader
from .created_by_ip import CreatedByIp
from .created_by_routing_data import CreatedByRoutingData
from .created_by_user_agent import CreatedByUserAgent
from .created_micro import CreatedMicro
from .datetime import DateTime
from .datetime_micro import DateTimeMicro
from .email import Email
from .float import Float
from .has_many import HasMany
from .has_one import HasOne
from .integer import Integer
from .json import JSON
from .many_to_many import ManyToMany
from .many_to_many_with_data import ManyToManyWithData
from .phone import Phone
from .select import Select
from .string import String
from .timestamp import Timestamp
from .updated import Updated
from .updated_micro import UpdatedMicro
from .uuid import UUID


def build_column_config(name, column_class, **kwargs):
    return (name, {**{"class": column_class}, **kwargs})


def audit(name, **kwargs):
    return build_column_config(name, Audit, **kwargs)


def belongs_to(name, **kwargs):
    return build_column_config(name, BelongsTo, **kwargs)


def boolean(name, **kwargs):
    return build_column_config(name, Boolean, **kwargs)


def category_tree(name, **kwargs):
    return build_column_config(name, CategoryTree, **kwargs)


def created(name, **kwargs):
    return build_column_config(name, Created, **kwargs)


def created_by_authorization_data(name, **kwargs):
    return build_column_config(name, CreatedByAuthorizationData, **kwargs)


def created_by_header(name, **kwargs):
    return build_column_config(name, CreatedByHeader, **kwargs)


def created_by_ip(name, **kwargs):
    return build_column_config(name, CreatedByIp, **kwargs)


def created_by_routing_data(name, **kwargs):
    return build_column_config(name, CreatedByRoutingData, **kwargs)


def created_by_user_agent(name, **kwargs):
    return build_column_config(name, CreatedByUserAgent, **kwargs)


def created_micro(name, **kwargs):
    return build_column_config(name, CreatedMicro, **kwargs)


def datetime(name, **kwargs):
    return build_column_config(name, DateTime, **kwargs)


def datetime_micro(name, **kwargs):
    return build_column_config(name, DateTimeMicro, **kwargs)


def email(name, **kwargs):
    return build_column_config(name, Email, **kwargs)


def float(name, **kwargs):
    return build_column_config(name, Float, **kwargs)


def has_many(name, **kwargs):
    return build_column_config(name, HasMany, **kwargs)


def has_one(name, **kwargs):
    return build_column_config(name, HasOne, **kwargs)


def integer(name, **kwargs):
    return build_column_config(name, Integer, **kwargs)


def json(name, **kwargs):
    return build_column_config(name, JSON, **kwargs)


def many_to_many(name, **kwargs):
    return build_column_config(name, ManyToMany, **kwargs)


def many_to_many_with_data(name, **kwargs):
    return build_column_config(name, ManyToManyWithData, **kwargs)


def phone(name, **kwargs):
    return build_column_config(name, Phone, **kwargs)


def select(name, **kwargs):
    return build_column_config(name, Select, **kwargs)


def string(name, **kwargs):
    return build_column_config(name, String, **kwargs)


def timestamp(name, **kwargs):
    return build_column_config(name, Timestamp, **kwargs)


def updated(name, **kwargs):
    return build_column_config(name, Updated, **kwargs)


def updated_micro(name, **kwargs):
    return build_column_config(name, UpdatedMicro, **kwargs)


def uuid(name, **kwargs):
    return build_column_config(name, UUID, **kwargs)


__all__ = [
    "build_column_config",
    "audit",
    "Audit",
    "belongs_to",
    "BelongsTo",
    "boolean",
    "Boolean",
    "category_tree",
    "CategoryTree",
    "Column",
    "created",
    "created_micro",
    "Created",
    "CreatdMicro",
    "created_by_authorization_data",
    "CreatedByAuthorizationData",
    "created_by_ip",
    "CreatedByIp",
    "created_by_user_agent",
    "CreatedByUserAgent",
    "CreatedMicro",
    "created_micro",
    "datetime",
    "datetime_micro",
    "DateTime",
    "DateTimeMicro",
    "email",
    "Email",
    "float",
    "Float",
    "has_many",
    "HasMany",
    "has_one",
    "HasOne",
    "integer",
    "Integer",
    "json",
    "JSON",
    "many_to_many",
    "ManyToMany",
    "many_to_many_with_data",
    "ManyToManyWithData",
    "phone",
    "Phone",
    "select",
    "Select",
    "string",
    "String",
    "updated",
    "updated_micro",
    "Updated",
    "UpdatedMicro",
    "uuid",
    "UUID",
]
