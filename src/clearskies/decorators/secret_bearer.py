from .merge import merge
from typing import List, Optional
from ..authentication import secret_bearer as secret_bearer_binding
def secret_bearer(
    secret: str = None,
    secret_key: str = None,
    header_prefix: str = None,
    environment_key: str = None,
    documentation_security_name: str = None,
):
    def wrap_in_application(function):
        secret_bearer = secret_bearer_binding(
            secret=secret,
            environment_key=environment_key,
            documentation_security_name=documentation_security_name,
            header_prefix=header_prefix,
            secret_key=secret_key,
        )
        return merge(function, authentication=secret_bearer)

    wrap_in_application.is_wrapped_application = True
    return wrap_in_application
