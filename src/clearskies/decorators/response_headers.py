from .merge import merge
from typing import Dict
def response_headers(response_headers: Dict[str, str]):
    def wrap_in_application(function):
        return merge(function, response_headers=response_headers)

    wrap_in_application.is_wrapped_application = True
    return wrap_in_application
