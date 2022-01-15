from ..application import Application
from ..handlers.callable import Callable
def convert_to_application(application):
    # this is very similar to .context.Context.extract_handler: we definitely have some overlap.
    # however, things are a bit simpler here, and this doesn't have as much "context" to work
    # with, so it's not yet clear how to make this DRY
    # The goal of this is to make sure we have an actual application, so users can have a bit
    # more flexibility about what they pass into the build_context method.

    # first, if it has the handler_class attribute, then just assume it is an application object
    if hasattr(application, 'handler_class'):
        return application

    # check for a dictionary with the same thing (in case the developer doesn't want to bother with
    # an application)
    if hasattr(application, '__getitem__') and 'handler_class' in application:
        if not 'handler_config' in application:
            raise ValueError(
                "build_context was passed a dictionary-like object with 'handler_class', but not " + \
                "'handler_config'.  Both are required to build an application"
            )
        return Application(application['handler_class'], application['handler_config'])

    # if we get a callable, then use the callable handler class
    if callable(application):
        return Application(Callable, {'callable': application})
