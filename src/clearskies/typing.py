from typing import Any, Callable

from clearskies.action import Action
from clearskies.query.condition import Condition
from clearskies.validator import Validator

action = Callable[..., dict[str, Any]] | Action
condition = str | Callable | Condition
join = str | Callable[..., str]
validator = Callable[..., str] | Validator
response = str | bytes | dict[str, Any] | list[Any]
