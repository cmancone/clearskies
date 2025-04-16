from ..binding_config import BindingConfig
from .auth0_jwks import Auth0JWKS
from .authorization import Authorization
from .authorization_pass_through import AuthorizationPassThrough
from .jwks import JWKS
from .jwks_jwcrypto import JWKSJwCrypto
from .public import Public, PublicAuth
from .secret_bearer import SecretBearer, SecretBearerAuth


def public():
    return BindingConfig(Public)


def secret_bearer(**kwargs):
    return BindingConfig(SecretBearerAuth, **kwargs)


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
    "PublicAuth",
    "secret_bearer",
    "SecretBearer",
    "SecretBearerAuth",
    "auth0_jwks",
    "Auth0JWKS",
    "authorization",
    "jwks",
    "JWKS",
    "jwks_jwcrypto",
    "JWKSJwCrypto",
]
