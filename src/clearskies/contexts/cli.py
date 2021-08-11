from ..authentication import public
from ..di import StandardDependencies
from ..input_outputs import CLI as CLIInputOutput
from ..input_outputs import exceptions
from .build_context import build_context
from .context import Context


class CLI(Context):
    def __init__(self, di):
        super().__init__(di)

    def finalize_handler_config(self, config):
        return {
            'authentication': public(),
            **config,
        }

    def __call__(self):
        if self._handler is None:
            raise ValueError("Cannot execute CLI context without first configuring it")

        try:
            return self._handler(self._di.build(CLIInputOutput))
        except exceptions.CLINotFound:
            print('help (aka 404 not found)!')

def cli(
    application,
    di_class=StandardDependencies,
    bindings=None,
    binding_classes=None,
    binding_modules=None
):
    return build_context(
        CLI,
        application,
        di_class,
        bindings=bindings,
        binding_classes=binding_classes,
        binding_modules=binding_modules
    )
