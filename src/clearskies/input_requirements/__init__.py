from ..binding_config import BindingConfig
from .minimum_length import MinimumLength
from .required import Required
from .maximum_length import MaximumLength


def minimum_length(minimum_length):
    return BindingConfig(MinimumLength, minimum_length)

def maximum_length(maximum_length):
    return BindingConfig(MaximumLength, maximum_length)

def required():
    return BindingConfig(Required)
