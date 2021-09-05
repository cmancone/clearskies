from .routing import Base
from abc import abstractmethod
from .simple_routing_route import SimpleRoutingRoute
from .. import autodoc


class SimpleRouting(Base):
    _routes = None

    _configuration_defaults = {
        'base_url': '',
        'authentication': None,
        'routes': [],
        'schema_route': '',
        'schema_configuration': {},
        'schema_format': autodoc.formats.oai3_json.OAI3JSON,
    }

    def __init__(self, di):
        super().__init__(di)

    def handle(self, input_output):
        request_method = input_output.get_request_method()
        full_path = input_output.get_full_path().strip('/')
        if self.configuration('schema_route') and self.configuration('schema_route') == full_path:
            return self.hosted_schema(input_output)

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

    def _finalize_configuration(self, configuration):
        configuration = super()._finalize_configuration(configuration)
        if 'schema_route' in configuration:
            configuration['schema_route'] = configuration['schema_route'].strip('/')
        return configuration

    def _build_routes(self, routes, authentication=None):
        self._routes = []
        for (i, route_config) in enumerate(routes):
            if route_config.get('application'):
                application = route_config.get('application')
                if not hasattr(application, 'handler_config') or not hasattr(application, 'handler_class'):
                    raise ValueError(f"A non application was passed in the 'application' key of route #{i+1}")
                route_config['handler_class'] = application.handler_class
                route_config['handler_config'] = application.handler_config
            if not route_config.get('handler_class'):
                raise ValueError(
                    "Each route must specify a handler class via 'handler_class' key, " + \
                    f"but 'handler_class' was missing for route #{i+1}"
                )
            if not route_config.get('handler_config'):
                raise ValueError(
                    "Each route must specify the handler configuration via 'handler_config' key, " + \
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

    def documentation(self):
        base_url = self.configuration('base_url')
        docs = []
        for route in self._routes:
            docs.extend(route.documentation(base_url))
        return docs

    def documentation_models(self):
        models = {}
        for route in self._routes:
            models = {**models, **route.documentation_models()}
        return models

    def hosted_schema(self, input_output):
        schema = self._di.build(self.configuration('schema_format'))
        schema.set_requests(self.documentation())
        schema.set_models(self.documentation_models())
        extra_schema_config = self.configuration('schema_configuration')
        if 'info' not in extra_schema_config:
            extra_schema_config['info'] = {
                "title": "Auto generated by clearskies",
                "version": "1.0"
            }
        return input_output.respond(schema.pretty(root_properties=extra_schema_config), 200)
