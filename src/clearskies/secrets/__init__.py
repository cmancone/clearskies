from .akeyless import AKeyless, AKeylessAdditionalConfig
from . import additional_configs
from ..binding_config import BindingConfig


def akeyless(*args, **kwargs):
    return BindingConfig(AKeyless, *args, **kwargs)


def akeyless_aws_iam_auth(access_id=None, api_host=None):
    return AKeylessAdditionalConfig("aws_iam", access_id=access_id, api_host=api_host)


def akeyless_saml_auth(access_id=None, api_host=None, profile=None):
    return AKeylessAdditionalConfig("saml", access_id=access_id, api_host=api_host, profile=profile)


def akeyless_jwt_auth(jwt_env_key, access_id=None, api_host=None):
    return AKeylessAdditionalConfig("jwt", jwt_env_key=jwt_env_key, access_id=access_id, api_host=api_host)


def akeyless_access_key_auth(access_id=None, api_host=None):
    return AKeylessAdditionalConfig("access_key", access_id=access_id, api_host=api_host)


__all__ = [
    "AKeyless",
    "additional_configs",
    "akeyless",
    "akeyless_aws_iam_auth",
    "akeyless_saml_auth",
    "akeyless_jwt_auth",
    "akeyless_access_key_auth",
]
