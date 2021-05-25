from ..binding_specs import BindingSpec
from ..input_outputs import WSGI as WSGIInputOutput


class WSGI:
    _object_graph = None
    _handler = None

    def __init__(self, object_graph):
        self._object_graph = object_graph

    def configure(self, application):
        self._handler = self._object_graph.provide(application.handler_class)
        self._handler.configure(application.handler_config)

    def __call__(self, env, start_response):
        if self._handler is None:
            raise ValueError("Cannot execute WSGI context without first configuring it")

        return self._handler(WSGIInputOutput(env, start_response))

def wsgi(application, binding_spec_class=BindingSpec):
    object_graph = binding_spec_class.get_object_graph()
    context = object_graph.provide(WSGI)
    context.configure(application)
    return context
