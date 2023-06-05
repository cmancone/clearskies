from ..handlers import callable as callable_module
class Context:
    di = None
    handler = None

    def __init__(self, di):
        self.di = di

    def configure(self, application):
        self.handler = self.extract_handler(application)

    def bind(self, key, value):
        self.di.bind(key, value)

    def build(self, key):
        return self.di.build(key)

    def mock_class(self, class_or_name, replacement):
        self.di.mock_class(class_or_name, replacement)

    def extract_handler(self, application):
        """
        This accepts the application passed in to the context and returns the handler

        Most importantly, it doesn't technically have to be an application: if passed a simple function
        it will assume you mean to use the callable handler, and if passed a dictionary with 'handler_class'
        and 'handler_config' keys, it will build a handler from that.
        """
        # applications will have a handler_class property
        if hasattr(application, 'handler_class'):
            handler = self.di.build(application.handler_class, cache=False)
            handler.configure(self.finalize_handler_config(application.handler_config))
            return handler

        # check for a dictionary with the same thing (in case the developer doesn't want to bother with
        # an application
        if hasattr(application, '__getitem__') and 'handler_class' in application:
            if not 'handler_config' in application:
                raise ValueError(
                    "context was passed a dictionary-like object with 'handler_class', but not " + \
                    "'handler_config'.  Both are required to execute the handler"
                )
            handler = self.di.build(application['handler_class'], cache=False)
            handler.configure(self.finalize_handler_config(application['handler_config']))
            return handler

        # if we get a callable, then use the callable handler class
        if callable(application):
            handler = self.di.build(callable_module.Callable, cache=False)
            handler.configure(self.finalize_handler_config({'callable': application}))
            return handler

        raise ValueError(
            "The context received an object it did not know how to handle!  You should pass in either an instance " + \
            "of clearskies.Application, a dictionary with 'handler_class' and 'handler_config' keys, or a " + \
            "function/lambda to be executed"
        )

    def finalize_handler_config(self, config):
        return config
