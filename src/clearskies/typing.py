from typing import Any, Callable

from clearskies.action import Action
from clearskies.validator import Validator

action = Callable[..., dict[str, Any]] | Action
condition = str | Callable[..., str]
validator = Callable[..., str] | Validator
