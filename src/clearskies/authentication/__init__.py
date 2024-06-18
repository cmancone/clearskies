from ..binding_config import BindingConfig
from .secret_bearer import SecretBearer
from .public import Public
from .auth0_jwks import Auth0JWKS
from .authorization import Authorization
from .jwks import JWKS
from .jwks_jwcrypto import JWKSJwCrypto
from .authorization_pass_through import AuthorizationPassThrough


def public():
    return BindingConfig(Public)


def secret_bearer(**kwargs):
    return BindingConfig(SecretBearer, **kwargs)


def auth0_jwks(**kwargs):
    return BindingConfig(Auth0JWKS, **kwargs)


def jwks(jwks_url, **kwargs):
    return BindingConfig(JWKS, jwks_url=jwks_url, **kwargs)


def jwks_jwcrypto(jwks_url, **kwargs):
    return BindingConfig(JWKSJwCrypto, jwks_url=jwks_url, **kwargs)


__all__ = [
    "Authorization",
    "AuthorizationPassThrough",
    "BindingConfig",
    "public",
    "Public",
    "secret_bearer",
    "SecretBearer",
    "auth0_jwks",
    "Auth0JWKS",
    "authorization",
    "jwks",
    "JWKS",
    "jwks_jwcrypto",
    "JWKSJwCrypto",
]
