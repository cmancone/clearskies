class Application:
    handler_class = None
    handler_config = None
    di_class = None
    bindings = None
    binding_classes = None
    binding_modules = None
    additional_configs = None

    def __init__(
        self,
        handler_class,
        handler_config,
        di_class=None,
        bindings=None,
        binding_classes=None,
        binding_modules=None,
        additional_configs=None,
    ):
        """
        This will probably need to do more eventually, but right now this will do it
        """
        self.handler_class = handler_class
        self.handler_config = handler_config
        self.di_class = di_class
        self.bindings = {} if bindings is None else bindings
        self.binding_classes = [] if binding_classes is None else binding_classes
        self.binding_modules = [] if binding_modules is None else binding_modules
        self.additional_configs = [] if additional_configs is None else additional_configs
