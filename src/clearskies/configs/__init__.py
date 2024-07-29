"""
This module helps classes declare their configuration parameters via properties

To use it, the class needs to include the clearskies.configs.Confirgurable in its parent chain and
then create properties as needed using the various classes in the clearskies.configs module.  Each
class represents a specific "kind" of configuration, has typing declared to help while writing code,
and runtime checks to verify configs while the application is (preferably) booting.

Each config accepts a `required` and `default` kwarg to assist with validation/construction of
the configuration

Data is stored in the `_config` property on the instance.

Usage:

```
from clearskies import configs

class MyConfigurableClass(configs.Configurable):
    name = configs.String()
    age = configs.Integer(required=True)
    property_with_default = configs.String(default='some value')

    def __init__(self, name, age, optional=None):
        self.name = name
        self.age = age

        # always call this after saving the confiuration values to the properties.
        # It will fill in default values for any properties that have a default and
        # are none, and it will raise a ValueError if there is a required property
        # that does not have a value.
        self.finalize_and_validate_configuration()


configured_thingie = MyConfigurableClass('Bob', 18)
print(configured_thingie.age) # prints: 18
print(configured_thingie.property_with_default) # prints: some value

invalid_thingie = MyConfigurableClass(18, 20) # raises a TypeError

also_invalid = MyConfigurableClass('', 18) # raises a ValueError
```

Finally, parameters_to_properties is a decorator that will take any parameters passed into the
decorated function and assign them as instance properties.  You can use this to skip some code,
especially if you have a lot of configuration parameters.  In the above example, you could simplify
it as:

```
from clearskies import configs

class MyConfigurableClass(configs.Configurable):
    name = configs.String()
    age = configs.Integer(required=True)
    property_with_default = configs.String(default='some value')

    @clearskies.configs.parameters_to_properties()
    def __init__(self, name: str, age: int, optional: string=None):
        self.finalize_and_validate_configuration()
```

"""
import inspect

import wrapt

from .actions import Actions
from .any import Any
from .boolean import Boolean
from .config import Config
from .configurable import Configurable
from .model_class import ModelClass
from .select import Select
from .string import String
from .validators import Validators


@wrapt.decorator
def parameters_to_properties(wrapped, instance, args, kwargs):
    if not instance:
        raise ValueError("The parameters_to_properties decorator only works for methods in classes, not plain functions")

    if args:
        wrapped_args = inspect.getfullargspec(wrapped)
        for (key, value) in zip(wrapped_args.args[1:], args):
            setattr(instance, key, value)

    for (key, value) in kwargs.items():
        setattr(instance, key, value)

    wrapped(*args, **kwargs)

__all__ = [
    "Actions",
    "Any",
    "Boolean",
    "Config",
    "Configurable",
    "ModelClass",
    "Select",
    "String",
    "Validators",
]
