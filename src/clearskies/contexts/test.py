from ..binding_specs import BindingSpec
from ..mocks import InputOutput
from ..backends import MemoryBackend
from datetime import datetime, timezone


class Test:
    _application = None
    _object_graph = None
    _handler = None
    _binding_spec = None
    input_output = None
    memory_backend = None
    now = None

    def __init__(self, object_graph):
        self._object_graph = object_graph
        # a standard "now" will make life easier in case the second changes mid-testing

    def configure(self, application, binding_spec):
        self._binding_spec = binding_spec
        self.now = datetime.now().replace(tzinfo=timezone.utc, microsecond=0)
        self._application = application
        self.input_output = self._object_graph.provide(InputOutput)
        self.memory_backend = self._object_graph.provide(MemoryBackend)
        self.memory_backend.silent_on_missing_tables(silent=True)

        self.bind('now', self.now)
        self.bind('cursor_backend', self.memory_backend)

    def __call__(self, method=None, body=None, headers=None, url=None):
        if body is not None:
            self.input_output.set_body(body)
        if headers is not None:
            self.input_output.set_request_headers(headers)
        if method is not None:
            self.input_output.set_request_method(method)
        if url is not None:
            self.input_output.set_request_url(url)

        self._handler = self._object_graph.provide(self._application.handler_class)
        self._handler.configure(self._application.handler_config)
        return self._handler(self.input_output)

    def bind(self, key, value):
        self._binding_spec.bind_local(key, value)

def test(application, binding_spec_class=BindingSpec):
    [binding_spec, object_graph] = binding_spec_class.get_binding_spec_and_object_graph()
    context = object_graph.provide(Test)
    context.configure(application, binding_spec)
    return context
