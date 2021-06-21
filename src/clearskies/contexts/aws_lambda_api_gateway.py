from ..input_outputs import AWSLambdaAPIGateway as AWSInputOutput
from ..di import StandardDependencies
from .build_context import build_context


class AWSLambdaAPIGateway:
    _di = None
    _handler = None

    def __init__(self, di):
        self._di = di

    def configure(self, application):
        self._handler = self._di.build(application.handler_class, cache=False)
        self._handler.configure(application.handler_config)

    def __call__(self, event, context):
        if self._handler is None:
            raise ValueError("Cannot execute AWSLambda context without first configuring it")

        return self._handler(AWSInputOutput(event, context))

    def bind(self, key, value):
        self._di.bind(key, value)

def aws_lambda_api_gateway(
    application,
    di_class=StandardDependencies,
    bindings=None,
    binding_classes=None,
    binding_modules=None
):
    return build_context(
        AWSLambdaAPIGateway,
        application,
        di_class,
        bindings=bindings,
        binding_classes=binding_classes,
        binding_modules=binding_modules
    )
