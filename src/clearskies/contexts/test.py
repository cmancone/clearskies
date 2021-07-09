from ..authentication import public
from ..mocks import InputOutput
from ..di import StandardDependencies
from ..backends import MemoryBackend
from datetime import datetime, timezone
from .build_context import build_context


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
        self.memory_backend = self.di.build(MemoryBackend, cache=False)
        self.memory_backend.silent_on_missing_tables(silent=True)

        self.di.bind('now', self.now)
        self.di.bind('cursor_backend', self.memory_backend)

    def __call__(self, method=None, body=None, headers=None, url=None, input_output=None):
        if self._application is None:
            raise ValueError("Cannot call the test context without an application")

        if input_output is None:
            input_output = InputOutput()
        if body is not None:
            input_output.set_body(body)
        if headers is not None:
            input_output.set_request_headers(headers)
        if method is not None:
            input_output.set_request_method(method)
        if url is not None:
            input_output.set_request_url(url)

        self._handler = self.di.build(self._application.handler_class, cache=False)
        self._handler.configure({
            **{'authentication': public()},
            **self._application.handler_config,
        })
        return self._handler(input_output)

    def bind(self, key, value):
        self.di.bind(key, value)

    def build(self, key):
        return self.di.build(key)

def test(
    application,
    di_class=StandardDependencies,
    bindings=None,
    binding_classes=None,
    binding_modules=None
):
    return build_context(
        Test,
        application,
        di_class,
        bindings=bindings,
        binding_classes=binding_classes,
        binding_modules=binding_modules
    )
