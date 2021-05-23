class Application:
    handler_class = None
    handler_config = None

    def __init__(self, handler_class, handler_config):
        """
        This will probably need to do more eventually, but right now this will do it
        """
        self.handler_class = handler_class
        self.handler_config = handler_config
