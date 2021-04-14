from .binding_spec import BindingSpec
from ..input_outputs import WSGI as WSGIInputOutput


class WSGI(BindingSpec):
    _wsgi_environment = None
    _wsgi_start_response = None

    def __init__(self, wsgi_environment, wsgi_start_response, **kwargs):
        super().__init__(**kwargs)
        self._wsgi_environment = wsgi_environment
        self._wsgi_start_response = wsgi_start_response

    def provide_input_output(self):
        pre_configured = self._fetch_pre_configured('input_output')
        if pre_configured is not None:
            return pre_configured

        return WSGIInputOutput(self._wsgi_environment, self._wsgi_start_response)
