from ..authentication import public
from ..mocks import InputOutput
from ..di import StandardDependencies
from ..backends import MemoryBackend
from datetime import datetime, timezone


class Test:
    _application = None
    _handler = None
    input_output = None
    memory_backend = None
    now = None

    def __init__(self, di):
        self.di = di

    def configure(self, application):
        self.now = datetime.now().replace(tzinfo=timezone.utc, microsecond=0)
        self._application = application
        self.input_output = InputOutput()
        self.memory_backend = self.di.build(MemoryBackend, cache=False)
        self.memory_backend.silent_on_missing_tables(silent=True)

        self.di.bind('now', self.now)
        self.di.bind('cursor_backend', self.memory_backend)

    def __call__(self, method=None, body=None, headers=None, url=None):
        if body is not None:
            self.input_output.set_body(body)
        if headers is not None:
            self.input_output.set_request_headers(headers)
        if method is not None:
            self.input_output.set_request_method(method)
        if url is not None:
            self.input_output.set_request_url(url)

        self._handler = self.di.build(self._application.handler_class, cache=False)
        self._handler.configure({
            **{'authentication': public()},
            **self._application.handler_config,
        })
        return self._handler(self.input_output)

    def bind(self, key, value):
        self.di.bind(key, value)

    def build(self, key):
        return self.di.build(key)

def test(application, di_class=StandardDependencies, bindings=None, binding_classes=None, binding_modules=None):
    if bindings is None:
        bindings = {}
    if binding_classes is None:
        binding_classes = []
    if binding_modules is None:
        binding_modules = []

    bindings = {
        **application.bindings,
        **bindings,
    }
    binding_classes = [
        *application.binding_classes,
        *binding_classes,
    ]
    binding_modules = [
        *application.binding_modules,
        *binding_modules
    ]

    di = di_class.init(*binding_classes, **bindings, modules=binding_modules)
    context = di.build(Test, cache=False)
    context.configure(application)
    return context
