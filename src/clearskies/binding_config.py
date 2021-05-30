import inspect


class BindingConfig:
    object_class = None
    args = None
    kwargs = None

    def __init__(self, object_class, *args, **kwargs):
        if not inspect.isclass(object_class):
            raise ValueError(
                f"The first parameter passed to BindingConfig must be a class, not '{object_class.__class__.__name__}'"
            )
        self.object_class = object_class
        self.args = args
        self.kwargs = kwargs
