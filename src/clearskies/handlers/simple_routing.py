from .base import Base
from abc import abstractmethod
from .simple_routing_route import SimpleRoutingRoute
from . import callable as callable_handler
from ..functional import string
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
        'schema_authentication': None
    }

    def __init__(self, di):
        super().__init__(di)

    def top_level_authentication_and_authorization(self, input_output, authentication=None):
        # Check for separate authentication on the schema route
        schema_authentication = self.configuration('schema_authentication')
        if schema_authentication:
            request_method = input_output.get_request_method()
            full_path = input_output.get_full_path().strip('/')
            if self.configuration('schema_route') and self.configuration('schema_route') == full_path:
                return super().top_level_authentication_and_authorization(input_output, schema_authentication)
        return super().top_level_authentication_and_authorization(input_output)

    def can_handle(self, full_path, request_method, is_cors=False):
        for route in self._routes:
            route_data = route.matches(full_path, request_method, is_cors=is_cors)
            if route_data is not None:
                return route_data
        return None

    def handle(self, input_output):
        request_method = input_output.get_request_method()
        full_path = input_output.get_full_path().strip('/')
        if self.configuration('schema_route') and self.configuration('schema_route') == full_path:
            return self.hosted_schema(input_output)

        if request_method == 'OPTIONS':
            return self.cors(input_output)

        for route in self._routes:
            route_data = route.matches(full_path, request_method)
            if route_data is None:
                continue
            input_output.add_routing_data(route_data)

            return route(input_output)

        return self.error(input_output, 'Page not found', 404)

    def cors(self, input_output):
        if not self._cors_header:
            return self.error(input_output, 'not found', 404)
        request_method = input_output.get_request_method()
        full_path = input_output.get_full_path().strip('/')
        for route in self._routes:
            route_data = route.matches(full_path, request_method, is_cors=True)
            if route_data is None:
                continue

            return route.cors(input_output)
        return self.error(input_output, 'Page not found', 404)

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)

        if not configuration.get('routes'):
            raise ValueError(f"'routes' must be a list of routes for the {self.__class__.__name__} handler")
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
        base_url = configuration.get('base_url')
        self._build_routes(
            configuration['routes'],
            base_url if base_url else '/',
            authentication=configuration.get('authentication'),
            response_headers=configuration.get('response_headers'),
            security_headers=configuration.get('security_headers'),
        )

    def _finalize_configuration(self, configuration):
        configuration = super()._finalize_configuration(configuration)
        if configuration.get('schema_route'):
            base_url = configuration.get('base_url')
            configuration['schema_route'] = (base_url.strip('/') + '/' +
                                             configuration['schema_route'].strip('/')).strip('/')
        if configuration.get('schema_authentication') is not None:
            configuration['schema_authentication'] = self._di.build(configuration['schema_authentication'])
        return configuration

    def _build_routes(self, routes, base_url, authentication=None, response_headers=None, security_headers=None):
        self._routes = []
        if base_url is None:
            base_url = ''
        for (i, route_config) in enumerate(routes):
            # in general the route should be a dictionary with the route configuration,
            # but there are two exceptions.  The first is a "plain" callable.  In that case,
            # wrap it in a callable handler and define the path from the name
            if type(route_config) != dict:
                if callable(route_config):
                    route_config = {
                        'path': route_config.__name__,
                        'handler_class': callable_handler.Callable,
                        'handler_config': {
                            'callable': route_config
                        }
                    }
                # the other option is an application with another simple routing handler, in which
                # case just skip the path (which is optional anyway)
                elif hasattr(route_config, 'handler_class') and hasattr(route_config, 'handler_config') and issubclass(
                    route_config.handler_class, SimpleRouting
                ):
                    route_config = {
                        'path': '',
                        'application': route_config,
                    }
            if type(route_config) != dict:
                raise ValueError(
                    f"Routing config expected a dictionary with route information but found something else for route #{i+1}"
                )
            path = route_config.get('path')
            if path is None:
                path = ''
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
            if route_config.get('handler_config') is None:
                raise ValueError(
                    "Each route must specify the handler configuration via 'handler_config' key, " + \
                    f"but 'handler_config' was missing for route #{i+1}"
                )
            route = SimpleRoutingRoute(self._di)
            route.configure(
                route_config['handler_class'],
                route_config['handler_config'],
                path=base_url.rstrip('/') + '/' + path.lstrip('/'),
                methods=route_config.get('methods'),
                authentication=authentication,
                response_headers=response_headers,
                security_headers=security_headers,
            )
            self._routes.append(route)

    def documentation(self):
        docs = []
        for route in self._routes:
            docs.extend(route.documentation())
        return docs

    def documentation_security_schemes(self):
        schemes = {}
        for route in self._routes:
            schemes = {**schemes, **route.documentation_security_schemes()}
        return schemes

    def documentation_models(self):
        models = {}
        for route in self._routes:
            models = {**models, **route.documentation_models()}
        return models

    def hosted_schema(self, input_output):
        schema = self._di.build(self.configuration('schema_format'))
        schema.set_requests(self.documentation())
        schema.set_components(self.documentation_components())
        extra_schema_config = self.configuration('schema_configuration')
        if 'info' not in extra_schema_config:
            extra_schema_config['info'] = {"title": "Auto generated by clearskies", "version": "1.0"}
        response_headers = self.configuration('response_headers')
        if response_headers:
            input_output.set_headers(response_headers)
        for security_header in self.configuration('security_headers'):
            security_header.set_headers_for_input_output(input_output)
        return input_output.respond(schema.pretty(root_properties=extra_schema_config), 200)
