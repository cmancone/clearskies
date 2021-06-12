from ..authentication import public
from ..di import StandardDependencies
from ..input_outputs import CLI as CLIInputOutput
from ..input_outputs import exceptions


class CLI:
    _di = None
    _handler = None

    def __init__(self, di):
        self._di = di

    def configure(self, application):
        self._handler = self._di.build(application.handler_class)
        self._handler.configure({
            **{'authentication': public()},
            **application.handler_config
        })

    def __call__(self):
        if self._handler is None:
            raise ValueError("Cannot execute CLI context without first configuring it")

        try:
            return self._handler(self._di.build(CLIInputOutput))
        except input_outputs.exceptions.CLINotFound:
            print('help (aka 404 not found)!')

    def bind(self, key, value):
        self._di.bind(key, value)

def cli(application, di_class=StandardDependencies, bindings=None, binding_classes=None, binding_modules=None):
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
    context = di.build(CLI, cache=False)
    context.configure(application)
    return context
