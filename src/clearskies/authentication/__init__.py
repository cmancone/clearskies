from ..binding_config import BindingConfig
from .secret_bearer import SecretBearer
from .public import Public
from .auth0_jwks import Auth0JWKS

def public():
    return BindingConfig(Public)

def secret_bearer(**kwargs):
    return BindingConfig(SecretBearer, **kwargs)

def auth0_jwks(**kwargs):
    return BindingConfig(Auth0JWKS, **kwargs)
