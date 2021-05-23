from ..binding_specs import BindingSpec
from ..mocks import InputOutput
from ..backends import MemoryBackend


class Test:
    _application = None
    _object_graph = None
    _handler = None
    _binding_spec = None
    input_output = None
    memory_backend = None

    def __init__(self, object_graph, binding_spec):
        self._object_graph = object_graph
        self._binding_spec = binding_spec

    def configure(self, application, binding_spec):
        self._application = application
        self.input_output = self.object_graph.provide(InputOutput)
        self.memory_backend = self.object_graph.provide(MemoryBackend)
        self.memory_backend.silent_on_missing_tables(silent=True)

    def __call__(self, method=None, body=None, headers=None, url=None):
        if body is not None:
            self._input_output.set_body(body)
        if headers is not None:
            self._input_output.set_request_headers(request_headers)
        if method is not None:
            self._input_output.set_request_method(request_method)
        if url is not None:
            self._input_output.set_request_url(request_url, script_name=script_name)

        self._handler = self._object_graph.provide(application.handler_class)
        self._handler.configure(application.handler_config)
        return self._handler(self.input_output)

    def bind(self, key, value):
        self._binding_spec.bind(key, value)

def test(application, binding_spec_class=BindingSpec):
    [binding_spec, object_graph] = binding_spec_class.get_binding_spec_and_object_graph()
    context = object_graph.provide(Testing)
    context.configure(application, binding_spec)
    return context
