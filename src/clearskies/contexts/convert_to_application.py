from ..application import Application
from ..handlers.callable import Callable
def convert_to_application(application, needs_routing=False):
    """
    Converts a variety of allowed inputs into an application which the context can run.

    This is called by the `build_context` method which is in turn used by all of the
    clearskies.context.* functions.  The goal is to provide flexibility to the developer.
    The context itself always runs an application.  However, we want to give the developer
    additional options.  This function marrys the two.  This function can specifically handle:

     1. A function
     2. A function with one or more clearskies.decorators.* applied to it
     3. A list containing any number of the above
     4. A clearskies.Application object
     5. A dictionary containing two keys: 'handler_class' and 'handler_config'

    Note that if more than one function is provided they will all be wrapped in a SimpleRouting
    handler.  In addition, if any of the functions don't have routing information provided
    by a decorator, then the the function name will be used as the route for the function
    and only the GET method will be allowed.
    """
    # Lists need some special processing, although they just end up back here in the end
    if type(application) == list:
        return convert_list_to_application(application)

    # if it has the handler_class attribute, then just assume it is an application object
    if hasattr(application, 'handler_class'):
        return add_routing(application) if needs_routing else application

    # check for a dictionary with the same thing (in case the developer doesn't want to bother with
    # an application)
    if hasattr(application, '__getitem__') and 'handler_class' in application:
        if not 'handler_config' in application:
            raise ValueError(
                "build_context was passed a dictionary-like object with 'handler_class', but not " + \
                "'handler_config'.  Both are required to build an application"
            )
        application = Application(application['handler_class'], application['handler_config'])
        return add_routing(application) if needs_routing else application

    # if we have a wrapped application, then it's a callable with decorators and we can invoke
    # it to return an application
    if hasattr(application, 'is_wrapped_application') and application.is_wrapped_application:
        return add_routing(application()) if needs_routing else application()

    # if we get a callable, then use the callable handler class
    if callable(application):
        application = Application(Callable, {'callable': application})
        return add_routing(application()) if needs_routing else application()

    raise ValueError(
        "A context was passed something but I'm not smart enough to figure out what it is :(  In general you want to pass in an Application, a callable, or a callable with decorators from the clearskies.decorators module.  You can also try a dictionary with `handler_class` and `handler_config` options.  I'll link to the docs eventually."
    )
