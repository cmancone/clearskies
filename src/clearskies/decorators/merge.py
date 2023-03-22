from ..application import Application
from ..handlers import callable as callable_handler
from ..handlers import simple_routing
from typing import Any, Dict, Set

routing_kwargs = ['path', 'methods']
binding_kwargs = ['bindings', 'binding_classes', 'binding_modules']
def merge(function: callable, **kwargs: Dict[str, Any]) -> Application:
    is_wrapped_application = getattr(function, 'is_wrapped_application', False)
    binding_configs = extract_binding_configs(kwargs)
    callable_configs = extract_callable_configs(kwargs)
    routing_configs = extract_routing_configs(kwargs)

    # if ths is the first decorator added then we need to wrap it in an application
    if not is_wrapped_application and type(function) != Application:
        application = Application(
            callable_handler.Callable,
            {
                **callable_configs, 'callable': function
            },
            **binding_configs,
        )
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
                **binding_configs,
            )
        # and then we are all done
        return application

    # if we got here then we have a wrapped application, which means that function will return an
    # application when called... except when it doesn't which has to do with nested decorators and
    # I'm too lazy to sort it out but the below works fine.
    if is_wrapped_application:
        application = function()
    else:
        application = function
    authentication = application.handler_config.get('authentication')

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
        for binding_name in binding_kwargs:
            if not getattr(application, binding_name):
                continue
            from_application = getattr(application, binding_name)
            from_configs = binding_configs.get(binding_name, {} if type(from_application) == dict else [])
            if type(from_application) == dict:
                binding_configs[binding_name] = {**from_application, **from_configs}
            else:
                binding_configs[binding_name] = [*from_application, *from_configs]
        return Application(
            simple_routing.SimpleRouting,
            {
                'authentication':
                authentication,
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
            **binding_configs,
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

    for binding_name in binding_kwargs:
        if binding_configs.get(binding_name):
            from_application = getattr(application, binding_name)
            from_configs = binding_configs[binding_name]
            if type(from_application) == dict:
                setattr(application, binding_name, {**from_application, **from_configs})
            else:
                setattr(application, binding_name, [*from_application, *from_configs])
    return application
def extract_callable_configs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """ Return the configuration settings from the kwargs which are valid for the callable handler. """
    # all configs execpt 'path' and 'methods' go with the callable
    return {key: kwargs[key] for key in kwargs.keys() if key not in routing_kwargs and key not in binding_kwargs}
def extract_routing_configs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """ Return the configuration settings from the kwargs which are valid for the routing info. """
    return {key: kwargs[key] for key in kwargs.keys() if key in routing_kwargs}
def extract_binding_configs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """ Return the configuration settings from the kwargs which are valid for bindings. """
    return {key: kwargs[key] for key in kwargs.keys() if key in binding_kwargs}
