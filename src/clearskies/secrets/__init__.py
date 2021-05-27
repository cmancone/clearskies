from .akeyless import AKeyless
from ..binding_config import BindingConfig


def akeyless(*args, **kwargs):
    return BindingConfig(AKeyless, *args, **kwargs)
