import inspect
import os
import types
from ..application import Application
from ..handlers.callable import Callable as CallableHandler
from ..handlers.simple_routing import SimpleRouting as SimpleRoutingHandler
from typing import Any, Callable, Dict, Union, List


def convert_to_application(
    application: Union[Application, Dict[str, Any], Callable, List[Callable], types.ModuleType]
) -> Application:
    """
    Converts a variety of allowed inputs into an application which the context can run.

    This is called by the `build_context` method which is in turn used by all of the
    clearskies.context.* functions.  The goal is to provide flexibility to the developer.
    The context itself always runs an application.  However, we want to give the developer
    additional options.  This function marrys the two.  This function can specifically handle:

     1. A module
     2. A function
     3. A function with one or more clearskies.decorators.* applied to it
     4. A list containing any number of the above
     5. A clearskies.Application object
     6. A dictionary containing two keys: 'handler_class' and 'handler_config'

    Note that if more than one function is provided they will all be wrapped in a SimpleRouting
    handler.  In addition, if any of the functions don't have routing information provided
    by a decorator, then the the function name will be used as the route for the function
    and only the GET method will be allowed.

    Finally, if passing in a module, note that only functions with routing decorators will be
    imported.  This stops you from accidentally taking helper functions and exposing them as endpoints.
    """
    if type(application) == types.ModuleType:
        return convert_module_to_application(application)

    # Lists need some special processing, although they just end up back here in the end
    if type(application) == list:
        return convert_list_to_application(application)

    # if it has the handler_class attribute, then just assume it is an application object
    if hasattr(application, "handler_class"):
        return application

    # check for a dictionary with the same thing (in case the developer doesn't want to bother with
    # an application)
    if hasattr(application, "__getitem__") and "handler_class" in application:
        if not "handler_config" in application:
            raise ValueError(
                "build_context was passed a dictionary-like object with 'handler_class', but not "
                + "'handler_config'.  Both are required to build an application"
            )
        return Application(application["handler_class"], application["handler_config"])

    # if we have a wrapped application, then it's a callable with decorators and we can invoke
    # it to return an application
    if getattr(application, "is_wrapped_application", False):
        return application if type(application) == Application else application()

    # if we get a callable, then use the callable handler class
    if callable(application):
        return Application(CallableHandler, {"callable": application})

    raise ValueError(
        "A context was passed something but I'm not smart enough to figure out what it is :(  In general you want to pass in an Application, a callable, or a callable with decorators from the clearskies.decorators module.  You can also try a dictionary with `handler_class` and `handler_config` options.  I'll link to the docs eventually."
    )


def convert_module_to_application(module: types.ModuleType) -> Application:
    """
    Take a module, find any routing applications in it, and convert it to a single application
    """
    if not hasattr(module, "__file__") or not module.__file__:
        raise ValueError("I'm trying to find routed functions in a module but I was passed a python-native module")
    root = os.path.dirname(module.__file__)
    checked = {}
    routes = convert_list_to_application(return_routed_functions(module, root, len(root), checked))
    return routes


def return_routed_functions(
    module: types.ModuleType, root: str, root_len: int, checked: [str, str]
) -> List[Application]:
    routed_functions = []
    for name, item in module.__dict__.items():
        if type(item) == Application:
            routed_functions.append(item)
            continue
        if getattr(item, "is_wrapped_application", False):
            routed_functions.append(item())
            continue
        if inspect.ismodule(item):
            if not hasattr(item, "__file__") or not item.__file__:
                continue
            child_root = os.path.dirname(item.__file__)
            if child_root[:root_len] != root:
                continue
            if item.__file__ in checked:
                continue
            checked[item.__file__] = True
            routed_functions.extend(return_routed_functions(item, root, root_len, checked))
    return routed_functions


def convert_list_to_application(applications: List[Union[Application, Callable]]) -> Application:
    """
    Take a list of applications and convert it into a single application.
    """
    # First check the items.  Only callables or SimpleRouting handlers are allowed.  Everything else is too complicated.
    for index, application in enumerate(applications):
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
    # also, our top level router will need something for authentication.  It's a requirement.  It doesn't
    # actually matter exactly _what_ it is because it won't overwrite authentication for the children.
    authentication = None
    for application in applications:
        converted = convert_to_application(application)
        if not authentication and converted.handler_config.get("authentication"):
            authentication = converted.handler_config.get("authentication")
        routes.append(ensure_routing(converted))
        for di_key in ["bindings", "binding_classes", "binding_modules", "additional_configs"]:
            di_value = getattr(application, di_key, None)
            if di_value:
                if di_key == "bindings":
                    di_config["bindings"] = {**di_config.get("bindings", {}), **di_value}
                else:
                    di_config[di_key] = [*di_config.get(di_key, []), *di_value]

    if not authentication:
        raise ValueError(
            "I couldn't find any authentication rules while auto-importing your routes.  Make sure an add an authentication decorator to your routes, even if it's just @clearskies.decorators.public"
        )

    return Application(
        SimpleRoutingHandler,
        {
            "authentication": authentication,
            "routes": [ensure_routing(convert_to_application(application)) for application in applications],
        },
        **di_config,
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
    if not application.handler_config.get("callable"):
        raise ValueError(
            "Huh, I should have an application with a callable handler class but it doesn't have a callable so I don't know what went wrong :("
        )
    name = application.handler_config["callable"].__name__
    if name == "<lambda>":
        raise ValueError(
            "A lambda was sent to the application for auto-routing, but since lambdas don't have names, I can't create the route for it.  To fix this, switch it out for a regular function, attach a decorator with a path, or manually wrap it in a SimpleRouting handler"
        )
    return Application(
        SimpleRoutingHandler,
        {
            "authentication": application.handler_config.get("authentication", None),
            "routes": [
                {
                    "path": name,
                    "handler_class": application.handler_class,
                    "handler_config": application.handler_config,
                }
            ],
        },
    )
