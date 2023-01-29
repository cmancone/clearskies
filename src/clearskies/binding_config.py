import inspect
class BindingConfig:
    """
    A class to help with dependency injection configuration by separating the declaration of a dependency
    from its initialization.

    This exists to allow dependencies to be more flexible by giving an easy way to configure
    a dependency without having to create it.  The BindingConfig class makes this happen by keeping track
    of the class for a dependency and its configuration.  This gets passed off to the dependency injection
    container, which the puts the two together to build the actual dependency when needed.  A class
    that is working with a BindingConfig object then declares its dependencies in the constructor
    as needed, and also defines a `configure` method that will be called after instantiation and
    will be passed in any configuration from the binding config.

    Example:
        Here's an example that might represent a class which can make API requests against different
        but related API endpoints::

            class MyApiService:
                def __init__(self, requests, environment):
                    self.requests = requests
                    self.environment = environment

                def configure(self, api_host=None):
                    # Was the host specified in the binding config?
                    if api_host is not None:
                        self.api_host = api_host
                    # if not, check in the environment
                    else:
                        self.api_host = self.environment.get('API_HOST')

                def make_request(self):
                    print('Making request to ' + self.api_host)
                    # more logic here of course

            def my_function(my_first_api_service, my_second_api_service):
                my_first_api_service.make_request()
                my_second_api_service.make_request()

            cli = clearskies.contexts.cli(
                my_function,
                bindings={
                    'my_first_api_service': clearskies.BindingConfig(MyApiService, api_host='first.example.com'),
                    'my_second_api_service': clearskies.BindingConfig(MyApiService, api_host='second.example.com'),
                },
            )
            cli()
            # prints
            # Making request to first.example.com
            # Making request to second.example.com

    Note that clearskies classes that make use of a BindingConfig for easy configuration often expose a function
    that returns the BindingConfig object.  This lets you explicitly declare the configuration options and
    also shortens the syntax (and makes it more readable).

    Example:
        In the above example, the module that contains the MyApiService might also declare this function::

            def my_api_service(api_host: str=None):
                return clearskies.BindingConfig(MyApiService, api_host=api_host)

    Example:
        And therefore configuring the application to use this service would instead look like this::

            cli = clearskies.contexts.cli(
                my_function,
                bindings={
                    'my_first_api_service': my_api_service(api_host='first.example.com'),
                    'my_second_api_service': my_api_service(api_host='second.example.com'),
                },
            )
            cli()
            # prints
            # Making request to first.example.com
            # Making request to second.example.com
    """
    def __init__(self, object_class: type, *args, **kwargs):
        if not inspect.isclass(object_class):
            raise ValueError(
                f"The first parameter passed to BindingConfig must be a class, not '{object_class.__class__.__name__}'"
            )
        self.object_class = object_class
        self.args = args
        self.kwargs = kwargs
