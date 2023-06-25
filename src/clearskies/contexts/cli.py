from ..authentication import public
from ..input_outputs import CLI as CLIInputOutput
from ..input_outputs import exceptions
from .build_context import build_context
from .context import Context


class CLI(Context):
    def __init__(self, di):
        super().__init__(di)

    def finalize_handler_config(self, config):
        return {
            "authentication": public(),
            **config,
        }

    def __call__(self):
        if self.handler is None:
            raise ValueError("Cannot execute CLI context without first configuring it")

        try:
            return self.handler(self.di.build(CLIInputOutput))
        except exceptions.CLINotFound:
            print("help (aka 404 not found)!")


def cli(
    application,
    di_class=None,
    bindings=None,
    binding_classes=None,
    binding_modules=None,
    additional_configs=None,
):
    return build_context(
        CLI,
        application,
        di_class=di_class,
        bindings=bindings,
        binding_classes=binding_classes,
        binding_modules=binding_modules,
        additional_configs=additional_configs,
    )
