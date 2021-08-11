from ..authentication import public
from ..mocks import InputOutput
from ..di import StandardDependencies
from ..backends import MemoryBackend
from datetime import datetime, timezone
from .build_context import build_context
from .context import Context
from .convert_to_application import convert_to_application


class Test(Context):
    application = None
    input_output = None
    memory_backend = None
    now = None

    def __init__(self, di):
        super().__init__(di)

    def configure(self, application):
        # so for the other contexts, the application is just a way to manage configuration,
        # and so gets promptly thrown away.  We actually want it though
        self.now = datetime.now().replace(tzinfo=timezone.utc, microsecond=0)
        self.application = convert_to_application(application)
        self.memory_backend = self.di.build(MemoryBackend, cache=False)
        self.memory_backend.silent_on_missing_tables(silent=True)

        self.di.bind('now', self.now)
        self.di.bind('cursor_backend', self.memory_backend)

    def __call__(self, method=None, body=None, headers=None, url=None, input_output=None):
        if self.application is None:
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

        self.handler = self.di.build(self.application.handler_class, cache=False)
        self.handler.configure({
            **{'authentication': public()},
            **self.application.handler_config,
        })
        return self.handler(input_output)

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
