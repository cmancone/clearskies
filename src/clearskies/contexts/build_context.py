from ..application import Application
from ..handlers.callable import Callable
from .convert_to_application import convert_to_application


def build_context(
    context_class,
    application,
    di_class,
    bindings=None,
    binding_classes=None,
    binding_modules=None,
):
    application = convert_to_application(application)

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
    context = di.build(context_class, cache=False)
    context.configure(application)
    return context
