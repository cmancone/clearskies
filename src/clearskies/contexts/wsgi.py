from ..input_outputs import WSGI as WSGIInputOutput
from ..di import StandardDependencies


class WSGI:
    _di = None
    _handler = None

    def __init__(self, di):
        self._di = di

    def configure(self, application):
        self._handler = self._di.build(application.handler_class, cache=False)
        self._handler.configure(application.handler_config)

    def __call__(self, env, start_response):
        if self._handler is None:
            raise ValueError("Cannot execute WSGI context without first configuring it")

        return self._handler(WSGIInputOutput(env, start_response))

def wsgi(application, di_class=StandardDependencies, bindings=None, binding_classes=None, binding_modules=None):
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
    context = di.build(WSGI, cache=False)
    context.configure(application)
    return context
