from .routing import Routing
from abc import abstractmethod
from .simple_routing_route import SimpleRoutingRoute


class SimpleRouting(Routing):
    _routes = None

    _configuration_defaults = {
        'base_url': '',
        'authentication': None,
        'routes': [],
    }

    def __init__(self, input_output, object_graph):
        super().__init__(input_output, object_graph)

    def handle(self):
        request_method = self._input_output.get_request_method()
        full_path = self._input_output.get_full_path().strip('/')
        for route in self._routes:
            if route.matches(full_path, request_method):
                return route()

        return self.error('Page not found', 404)

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
            authorization=configuration.get('authorization'),
        )

    def _build_routes(self, routes, authorization=None):
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
            route = SimpleRoutingRoute(self._object_graph)
            route.configure(
                route_config['handler_class'],
                route_config['handler_config'],
                path=route_config.get('path'),
                method=route_config.get('method'),
                authorization=authorization,
            )
            self._routes.append(SimpleRoutingRoute(self._object_graph, route))
