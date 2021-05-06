from ..binding_config import BindingConfig
from .secret_bearer import SecretBearer
from .public import Public

def public():
    return BindingConfig(Public)

def secret_bearer(**kwargs):
    return BindingConfig(SecretBearer, **kwargs)
