from .merge import merge
from typing import List, Optional
from ..authentication import auth0_jwks as auth0_jwks_binding


def auth0_jwks(
    auth0_domain: str,
    audience: str,
    algorithms: Optional[List[str]] = None,
    documentation_security_name: Optional[str] = None,
):
    def wrap_in_application(function):
        auth0 = auth0_jwks_binding(
            auth0_domain=auth0_domain,
            audience=audience,
            algorithms=algorithms,
            documentation_security_name=documentation_security_name,
        )
        return merge(function, authentication=auth0)

    wrap_in_application.is_wrapped_application = True
    return wrap_in_application
