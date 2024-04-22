import datetime

from .after import After
from .before import Before
from ..binding_config import BindingConfig
from .minimum_length import MinimumLength
from .minimum_value import MinimumValue
from .maximum_length import MaximumLength
from .maximum_value import MaximumValue
from .required import Required
from .requirement import Requirement
from .unique import Unique
from .in_the_future_at_least import InTheFutureAtLeast
from .in_the_future_at_most import InTheFutureAtMost
from .in_the_past_at_least import InThePastAtLeast
from .in_the_past_at_most import InThePastAtMost
from .time_delta import TimeDelta


def after(other_column_name: str, allow_equal: bool = False):
    return BindingConfig(After, other_column_name=other_column_name, allow_equal=allow_equal)


def before(other_column_name: str, allow_equal: bool = False):
    return BindingConfig(Before, other_column_name=other_column_name, allow_equal=allow_equal)


def minimum_length(minimum_length: int):
    return BindingConfig(MinimumLength, minimum_length)


def minimum_value(minimum_value: int):
    return BindingConfig(MinimumValue, minimum_value)


def maximum_length(maximum_length: int):
    return BindingConfig(MaximumLength, maximum_length)


def maximum_value(maximum_value: int):
    return BindingConfig(MaximumValue, maximum_value)


def required():
    return BindingConfig(Required)


def unique():
    return BindingConfig(Unique)


def in_the_future_at_least(time_delta: datetime.timedelta):
    return BindingConfig(InTheFutureAtLeast, time_delta)


def in_the_future_at_most(time_delta: datetime.timedelta):
    return BindingConfig(InTheFutureAtMost, time_delta)


def in_the_past_at_least(time_delta: datetime.timedelta):
    return BindingConfig(InThePastAtLeast, time_delta)


def in_the_past_at_most(time_delta: datetime.timedelta):
    return BindingConfig(InThePastAtMost, time_delta)


__all__ = [
    "in_the_future_at_least",
    "in_the_future_at_most",
    "in_the_past_at_least",
    "in_the_past_at_most",
    "minimum_length",
    "maximum_length",
    "required",
    "TimeDelta",
    "unique",
]
