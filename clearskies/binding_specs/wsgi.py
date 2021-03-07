from .binding_spec import BindingSpec
from ..input_outputs import WSGI as WSGIInputOutput


class WSGI(BindingSpec):
    _wsgi_env = None
    _wsgi_start_response = None

    def __init__(self, wsgi_env, wsgi_start_response):
        self._wsgi_env = wsgi_env
        self._wsgi_start_response = wsgi_start_response

    def provide_input_output(self):
        return WSGIInputOutput(self._wsgi_env, self._wsgi_start_response)
