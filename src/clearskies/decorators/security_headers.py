from .merge import merge
from typing import List, Optional


def security_headers(*args):
    def wrap_in_application(function):
        return merge(function, security_headers=args)

    wrap_in_application.is_wrapped_application = True
    return wrap_in_application
