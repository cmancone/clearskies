from .merge import merge
from typing import List, Optional
from ..authentication import public as public_binding


def public():
    def wrap_in_application(function):
        return merge(function, authentication=public_binding())

    wrap_in_application.is_wrapped_application = True
    return wrap_in_application
