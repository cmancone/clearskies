from ..application import Application
from ..handlers import callable as callable_handler
from ..handlers import simple_routing
from typing import Any, Dict, Set
def merge(function: callable, **kwargs: Dict[str, Any]) -> Application:
    is_wrapped_application = getattr(function, 'is_wrapped_application', False)
    callable_configs = extract_callable_configs(kwargs)
    routing_configs = extract_routing_configs(kwargs)

    # if ths is the first decorator added then we need to wrap it in an application
    if not is_wrapped_application and type(function) != Application:
        application = Application(callable_handler.Callable, {**callable_configs, 'callable': function})
        # and if we have a route then we also want to wrap it in a router. Note that
        # there is a possible future issue in here and things will break if path
        # and methods are not specified at the same time.
        if 'path' in kwargs:
            application = Application(
                simple_routing.SimpleRouting,
                {
                    'routes': [
                        {
                            **routing_configs,
                            'handler_class': application.handler_class,
                            'handler_config': application.handler_config,
                        },
                    ],
                },
            )
        # and then we are all done
        return application

    # if we got here then we have a wrapped application, which means that function will return an
    # application when called..  Therefore, we need to call the function to return the inner application
    if is_wrapped_application:
        application = function()
    else:
        application = function

    # Next question: is there a path in our kwargs?  If so then we are trying to add routing to
    # the application.
    if 'path' in kwargs:
        # before we add routing, make sure we're not double routing
        if application.handler_class == simple_routing.SimpleRouting:
            raise ValueError(
                "Error applying decorators: it looks like more than one routing decorator was added to a function"
            )
        # Now then, wrap the application in a router.  For the inner application,
        # merge any configurations for the callable
        return Application(
            simple_routing.SimpleRouting,
            {
                'routes': [
                    {
                        **routing_configs,
                        'handler_class': application.handler_class,
                        'handler_config': {
                            **application.handler_config,
                            **callable_configs,
                        },
                    },
                ],
            },
        )

    # if we got here then we just need to merge in our callable configs.  The only trick is
    # whether or not we have an outer routing application.
    if application.handler_class == simple_routing.SimpleRouting:
        application.handler_config['routes'][0]['handler_config'] = {
            **application.handler_config['routes'][0]['handler_config'],
            **callable_configs,
        }

    else:
        application.handler_config = {**application.handler_config, **callable_configs}

    return application
routing_kwargs = ['path', 'methods']
def extract_callable_configs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """ Return the configuration settings from the kwargs which are valid for the callable handler. """
    # all configs execpt 'path' and 'methods' go with the callable
    return {key: kwargs[key] for key in kwargs.keys() if key not in routing_kwargs}
def extract_routing_configs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """ Return the configuration settings from the kwargs which are valid for the routing info. """
    return {key: kwargs[key] for key in kwargs.keys() if key in routing_kwargs}
