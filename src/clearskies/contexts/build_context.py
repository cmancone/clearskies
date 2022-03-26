from ..application import Application
from ..di import StandardDependencies
from ..handlers.callable import Callable
from .convert_to_application import convert_to_application
import sys
def build_context(
    context_class,
    application,
    di_class=None,
    bindings=None,
    binding_classes=None,
    binding_modules=None,
    additional_configs=None,
    additional_kwargs=None,
):
    application = convert_to_application(application)

    if di_class is None:
        di_class = application.di_class if application.di_class is not None else StandardDependencies

    if bindings is None:
        bindings = {}
    if binding_classes is None:
        binding_classes = []
    if binding_modules is None:
        binding_modules = []
    if additional_configs is None:
        additional_configs = []
    if additional_kwargs is None:
        additional_kwargs = {}

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
        *binding_modules,
    ]
    additional_configs = [
        *application.additional_configs,
        *additional_configs,
    ]

    di = di_class.init(*binding_classes, **bindings, modules=binding_modules, additional_configs=additional_configs)
    context = di.build(context_class, cache=False)
    context.configure(application, **additional_kwargs)
    return context
