from typing import Any, Callable

from clearskies.action import Action
from clearskies.validator import Validator
from clearskies.query.condition import Condition

action = Callable[..., dict[str, Any]] | Action
condition = str | Callable[..., str | Condition] | Condition
join = str | Callable[..., str]
validator = Callable[..., str] | Validator
response = str | bytes | dict[str, Any] | list[Any]
