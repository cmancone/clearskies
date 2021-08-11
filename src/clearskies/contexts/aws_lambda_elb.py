from ..input_outputs import AWSLambdaELB as AWSLambdaELBInputOutput
import clearskies
from .build_context import build_context
from .context import Context


class AWSLambdaELB(Context):
    def __init__(self, di):
        super().__init__(di)

    def __call__(self, event, context):
        if self.handler is None:
            raise ValueError("Cannot execute AWSLambdaELB context without first configuring it")

        return self.handler(AWSLambdaELBInputOutput(event, context))

def aws_lambda_elb(
    application,
    di_class=clearskies.di.StandardDependencies,
    bindings=None,
    binding_classes=None,
    binding_modules=None
):
    return build_context(
        AWSLambdaELB,
        application,
        di_class,
        bindings=bindings,
        binding_classes=binding_classes,
        binding_modules=binding_modules
    )
