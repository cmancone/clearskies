"""
This module helps classes declare their configuration parameters via properties.

To use it, the class needs to include the clearskies.configs.Confirgurable in its parent chain and
then create properties as needed using the various classes in the clearskies.configs module.  Each
class represents a specific "kind" of configuration, has typing declared to help while writing code,
and runtime checks to verify configs while the application is (preferably) booting.

Each config accepts a `required` and `default` kwarg to assist with validation/construction of
the configuration

Data is stored in the `_config` property on the instance.

Usage:

```python
from clearskies import configs


class MyConfigurableClass(configs.Configurable):
    name = configs.String()
    age = configs.Integer(required=True)
    property_with_default = configs.String(default="some value")

    def __init__(self, name, age, optional=None):
        self.name = name
        self.age = age

        # always call this after saving the confiuration values to the properties.
        # It will fill in default values for any properties that have a default and
        # are none, and it will raise a ValueError if there is a required property
        # that does not have a value.
        self.finalize_and_validate_configuration()


configured_thingie = MyConfigurableClass("Bob", 18)
print(configured_thingie.age)  # prints: 18
print(configured_thingie.property_with_default)  # prints: some value

invalid_thingie = MyConfigurableClass(18, 20)  # raises a TypeError

also_invalid = MyConfigurableClass("", 18)  # raises a ValueError
```

Finally, parameters_to_properties is a decorator that will take any parameters passed into the
decorated function and assign them as instance properties.  You can use this to skip some code,
especially if you have a lot of configuration parameters.  In the above example, you could simplify
it as:

```python
from clearskies import configs


class MyConfigurableClass(configs.Configurable):
    name = configs.String()
    age = configs.Integer(required=True)
    property_with_default = configs.String(default="some value")

    @clearskies.parameters_to_properties()
    def __init__(self, name: str, age: int, optional: string = None):
        self.finalize_and_validate_configuration()
```

"""

import inspect

from .actions import Actions
from .any import Any
from .any_dict import AnyDict
from .any_dict_or_callable import AnyDictOrCallable
from .authentication import Authentication
from .authorization import Authorization
from .boolean import Boolean
from .boolean_or_callable import BooleanOrCallable
from .callable_config import Callable
from .columns import Columns
from .conditions import Conditions
from .config import Config
from .datetime import Datetime
from .datetime_or_callable import DatetimeOrCallable
from .endpoint import Endpoint
from .float import Float
from .float_or_callable import FloatOrCallable
from .integer import Integer
from .integer_or_callable import IntegerOrCallable
from .joins import Joins
from .list_any_dict import ListAnyDict
from .list_any_dict_or_callable import ListAnyDictOrCallable
from .model_class import ModelClass
from .model_column import ModelColumn
from .model_columns import ModelColumns
from .model_destination_name import ModelDestinationName
from .model_to_id_column import ModelToIdColumn
from .readable_model_column import ReadableModelColumn
from .readable_model_columns import ReadableModelColumns
from .schema import Schema
from .searchable_model_columns import SearchableModelColumns
from .security_headers import SecurityHeaders
from .select import Select
from .select_list import SelectList
from .string import String
from .string_dict import StringDict
from .string_list import StringList
from .string_list_or_callable import StringListOrCallable
from .string_or_callable import StringOrCallable
from .timedelta import Timedelta
from .timezone import Timezone
from .url import Url
from .validators import Validators
from .writeable_model_column import WriteableModelColumn
from .writeable_model_columns import WriteableModelColumns

__all__ = [
    "Actions",
    "Any",
    "AnyDict",
    "AnyDictOrCallable",
    "Authentication",
    "Authorization",
    "Boolean",
    "BooleanOrCallable",
    "Callable",
    "Columns",
    "Conditions",
    "Config",
    "Datetime",
    "DatetimeOrCallable",
    "Float",
    "FloatOrCallable",
    "Joins",
    "Integer",
    "IntegerOrCallable",
    "ListAnyDict",
    "ListAnyDictOrCallable",
    "ModelClass",
    "ModelColumn",
    "ModelColumns",
    "ModelToIdColumn",
    "ModelDestinationName",
    "ReadableModelColumn",
    "ReadableModelColumns",
    "Schema",
    "SearchableModelColumns",
    "SecurityHeaders",
    "Select",
    "SelectList",
    "String",
    "StringDict",
    "StringList",
    "StringListOrCallable",
    "StringOrCallable",
    "Timedelta",
    "Timezone",
    "Url",
    "Validators",
    "WriteableModelColumn",
    "WriteableModelColumns",
]
