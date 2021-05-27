from ..authentication import public
from ..binding_specs import BindingSpec
from ..input_outputs import CLI as CLIInputOutput


class CLI:
    _object_graph = None
    _binding_spec = None
    _handler = None

    def __init__(self, object_graph, binding_spec):
        self._object_graph = object_graph
        self._binding_spec = binding_spec

    def configure(self, application):
        self._handler = self._object_graph.provide(application.handler_class)
        config = {
            **{'authentication': public()},
            **application.handler_config
        }
        self._handler.configure(config)

    def __call__(self):
        if self._handler is None:
            raise ValueError("Cannot execute WSGI context without first configuring it")

        return self._handler(self._object_graph.provide(CLIInputOutput))

    def bind(self, key, value):
        self._binding_spec.bind_local(key, value)

def cli(application, binding_spec_class=BindingSpec, bindings=None, binding_classes=None):
    if bindings is None:
        bindings = {}
    if binding_classes is None:
        binding_classes = []
    bindings = {
        **application.bindings,
        **bindings,
    }
    binding_classes = [
        *application.binding_classes,
        *binding_classes,
    ]

    object_graph = binding_spec_class.get_object_graph(bindings=bindings, binding_classes=binding_classes)
    context = object_graph.provide(CLI)
    context.configure(application)
    return context
