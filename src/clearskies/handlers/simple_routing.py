from .routing import Base
from abc import abstractmethod
from .simple_routing_route import SimpleRoutingRoute


class SimpleRouting(Base):
    _routes = None

    _configuration_defaults = {
        'base_url': '',
        'authentication': None,
        'routes': [],
    }

    def __init__(self, di):
        super().__init__(di)

    def handle(self, input_output):
        request_method = input_output.get_request_method()
        full_path = input_output.get_full_path().strip('/')
        for route in self._routes:
            if route.matches(full_path, request_method):
                return route(input_output)

        return self.error(input_output, 'Page not found', 404)

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)

        if not configuration.get('routes'):
            raise ValueError(
                f"'routes' must be a list of routes for the {self.__class__.__name__} handler"
            )
        if not hasattr(configuration['routes'], '__iter__'):
            raise ValueError(
                f"'routes' must be a list of routes for the {self.__class__.__name__} handler, " + \
                'but a non-iterable was provided instead'
            )
        if isinstance(configuration['routes'], str):
            raise ValueError(
                f"'routes' must be a list of routes for the {self.__class__.__name__} handler, " + \
                'but a string was provided instead'
            )

        # we're actually going to build our routes, which will implicitly check the configuration too
        self._build_routes(
            configuration['routes'],
            authentication=configuration.get('authentication'),
        )

    def _build_routes(self, routes, authentication=None):
        self._routes = []
        for (i, route_config) in enumerate(routes):
            if not route_config.get('handler_class'):
                raise ValueError(
                    "Each route must specify a handler class via 'handler_class', " + \
                    f"but 'handler_class' was missing for route #{i+1}"
                )
            if not route_config.get('handler_config'):
                raise ValueError(
                    "Each route must specify the handler configuration via 'handler_config', " + \
                    f"but 'handler_config' was missing for route #{i+1}"
                )
            route = SimpleRoutingRoute(self._di)
            route.configure(
                route_config['handler_class'],
                route_config['handler_config'],
                path=route_config.get('path'),
                methods=route_config.get('methods'),
                authentication=authentication,
            )
            self._routes.append(route)
