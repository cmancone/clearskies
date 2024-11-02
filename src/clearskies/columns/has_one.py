from typing import Callable, List, Optional, Union


from clearskies import configs, parameters_to_properties
from clearskies.bindings import Action as BindingAction
from clearskies.actions import Action
from clearskies.bindings import Validator as BindingValidator
from clearskies.columns.validators import Validator
from clearskies.columns import has_many


class HasOne(has_many.HasMany):
    pass
