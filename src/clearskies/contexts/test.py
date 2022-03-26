from ..authentication import public
from ..mocks import InputOutput
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

    def configure(self, application, cursor_backend_to_memory_backend=True):
        # so for the other contexts, the application is just a way to manage configuration,
        # and so gets promptly thrown away.  We actually want it though
        self.now = datetime.now().replace(tzinfo=timezone.utc, microsecond=0)
        self.application = convert_to_application(application)
        self.memory_backend = self.di.build(MemoryBackend, cache=False)
        self.memory_backend.silent_on_missing_tables(silent=True)

        self.di.bind('now', self.now)
        if cursor_backend_to_memory_backend:
            self.di.bind('cursor_backend', self.memory_backend)

    def __call__(
        self,
        method=None,
        body=None,
        headers=None,
        url=None,
        routing_data=None,
        input_output=None,
        query_parameters=None
    ):
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
        if routing_data is not None:
            input_output.set_routing_data(routing_data)
        if query_parameters is not None:
            input_output.set_query_parameters(query_parameters)

        self.handler = self.di.build(self.application.handler_class, cache=False)
        self.handler.configure({
            **{
                'authentication': public()
            },
            **self.application.handler_config,
        })
        return self.handler(input_output)
def test(
    application,
    di_class=None,
    bindings=None,
    binding_classes=None,
    binding_modules=None,
    additional_configs=None,
    cursor_backend_to_memory_backend=True,
):
    return build_context(
        Test,
        application,
        di_class=di_class,
        bindings=bindings,
        binding_classes=binding_classes,
        binding_modules=binding_modules,
        additional_configs=additional_configs,
        additional_kwargs={'cursor_backend_to_memory_backend': cursor_backend_to_memory_backend}
    )
