from .binding_spec import BindingSpec
from ..input_outputs import WSGI as WSGIInputOutput


class WSGI(BindingSpec):
    _wsgi_environment = None
    _wsgi_start_response = None

    def __init__(self, wsgi_environment, wsgi_start_response):
        self._wsgi_environment = wsgi_environment
        self._wsgi_start_response = wsgi_start_response

    def provide_input_output(self):
        return WSGIInputOutput(self._wsgi_environment, self._wsgi_start_response)

    @classmethod
    def wsgi_endpoint(cls, wsgi_environment, wsgi_start_response, handler_class, handler_config):
        object_graph = cls.get_object_graph(wsgi_environment, wsgi_start_response)
        handler = object_graph.provide(handler_class)
        handler.configure(handler_config)
        return handler
