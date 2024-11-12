from typing import Any, Callable

from clearskies.action import Action
from clearskies.validator import Validator
from clearskies.bindings import Action as BindingAction
from clearskies.bindings import Validator as BindingValidator

action = Callable[..., dict[str, Any]] | Action | BindingAction
condition = str | Callable[..., str]
validator = Callable[..., str] | Validator | BindingValidator
