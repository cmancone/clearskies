from .merge import merge
from typing import List, Optional
from ..authentication import jwks as jwks_binding


def jwks(
    jwks_url: str,
    audience: Optional[str] = None,
    issuer: Optional[str] = None,
    algorithms: Optional[List[str]] = None,
    documentation_security_name: Optional[str] = None,
    jwks_cache_time: Optional[int] = None,
):
    def wrap_in_application(function):
        auth0 = jwks_binding(
            jwks_url=jwks_url,
            audience=audience,
            issuer=issuer,
            algorithms=algorithms,
            documentation_security_name=documentation_security_name,
            jwks_cache_time=jwks_cache_time,
        )
        return merge(function, authentication=auth0)

    wrap_in_application.is_wrapped_application = True
    return wrap_in_application
