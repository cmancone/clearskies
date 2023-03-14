from ..application import Application
from ..handlers.callable import Callable as CallableHandler
from ..handlers.simple_routing import SimpleRouting as SimpleRoutingHandler
from typing import Any, Callable, Dict, Union, List
def convert_to_application(application: Union[Application, Dict[str, Any], Callable, List[Callable]]) -> Application:
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

    # if we have a wrapped application, then it's a callable with decorators and we can invoke
    # it to return an application
    if getattr(application, 'is_wrapped_application', False):
        return application if type(application) == Application else application()

    # if we get a callable, then use the callable handler class
    if callable(application):
        Application(CallableHandler, {'callable': application})

    raise ValueError(
        "A context was passed something but I'm not smart enough to figure out what it is :(  In general you want to pass in an Application, a callable, or a callable with decorators from the clearskies.decorators module.  You can also try a dictionary with `handler_class` and `handler_config` options.  I'll link to the docs eventually."
    )
def convert_list_to_application(applications: List[Union[Application, Callable]]) -> Application:
    """
    Handle processing a list is passed into the convert_to_application function
    """
    # First check the items.  Only callables or SimpleRouting handlers are allowed.  Everything else is too complicated.
    for (index, application) in enumerate(applications):
        if not callable(application) and application.handler_class not in [CallableHandler, SimpleRoutingHandler]:
            raise ValueError(
                f"A context was provided with a list of applications, but in this case all the applications must be callables or wrapped in a SimpleRouting function.  Item #{index+1} was not either of these things."
            )

    # so this is... less than ideal.  In their current iteration, the simple router ignores any DI configuration
    # on inner applications (bindings, imported modules, imported classes, etc...).  To some extent this is
    # a short coming of how DI is handled, since all the applications share a single DI container.  If needed,
    # we can adjust things in the future so that each application may be called with its own DI container.
    # I'm avoiding that at the moment because it's not clear if it is necessary, and it will impact performance.
    # In the meantime, we need to collect DI configuration from our inner applications and combine those
    # in the outer one.
    di_config = {}
    routes = []
    for application in applications:
        converted = convert_to_application(application)
        routes.append(ensure_routing(converted))
        for di_key in ['bindings', 'binding_classes', 'binding_modules', 'additional_configs']:
            di_value = getattr(application, di_key)
            if di_value:
                if di_key == 'bindings':
                    di_config['bindings'] = {**di_config.get('bindings', {}), **di_value}
                else:
                    di_config[di_key] = [*di_config.get(di_key, []), *di_value]

    return Application(
        SimpleRoutingHandler,
        {'routes': [ensure_routing(convert_to_application(application)) for application in applications]}, **di_config
    )
def ensure_routing(application: Application) -> Application:
    """
    Add routing to an application by wrapping it in a SimpleRouting handler if it isn't already.
    """
    if application.handler_class == SimpleRoutingHandler:
        return application

    # We're making assumptions which is bad, but at this point in time the `application` should literally be
    # an application and it should either be a SimpleRoutingHnadler (which we took care of above) or it
    # should be a callable application. To add routing we wrap it in a SimpleRouting handler and use the callable
    # name as the route.  Still, let's just check even if it isn't the most meanginful error message.
    if not application.handler_config.get('callable'):
        raise ValueError(
            "Huh, I should have an application with a callable handler class but it doesn't have a callable so I don't know what went wrong :("
        )
    name = application.handler_config['callable'].__name__
    if name == '<lambda>':
        raise ValueError(
            "A lambda was sent to the application for auto-routing, but since lambdas don't have names, I can't create the route for it.  To fix this, switch it out for a regular function, attach a decorator with a path, or manually wrap it in a SimpleRouting handler"
        )
    return Application(
        SimpleRouting, {
            'routes': [{
                'path': name,
                'handler_class': application.handler_class,
                'handler_config': application.handler_config,
            }]
        }
    )
