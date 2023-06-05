from .merge import merge
from typing import List, Optional
def authorization(auth_rules):
    def wrap_in_application(function):
        return merge(function, authorization=auth_rules)

    wrap_in_application.is_wrapped_application = True
    return wrap_in_application
