class BindingConfig:
    object_class = None
    args = None
    kwargs = None

    def __init__(self, object_class, *args, **kwargs):
        self.object_class = object_class
        self.args = args
        self.kwargs = kwargs
