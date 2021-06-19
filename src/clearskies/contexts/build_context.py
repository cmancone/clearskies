def build_context(
    context_class,
    application,
    di_class,
    bindings=None,
    binding_classes=None,
    binding_modules=None,
):
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
