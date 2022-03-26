from ..input_outputs import WSGI as WSGIInputOutput
from .build_context import build_context
from .context import Context
class WSGI(Context):
    def __init__(self, di):
        super().__init__(di)

    def __call__(self, env, start_response):
        if self.handler is None:
            raise ValueError("Cannot execute WSGI context without first configuring it")

        return self.handler(WSGIInputOutput(env, start_response))
def wsgi(
    application,
    di_class=None,
    bindings=None,
    binding_classes=None,
    binding_modules=None,
    additional_configs=None,
):
    return build_context(
        WSGI,
        application,
        di_class=None,
        bindings=bindings,
        binding_classes=binding_classes,
        binding_modules=binding_modules,
        additional_configs=additional_configs,
    )
