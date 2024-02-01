import logging
import urllib.parse
import re
import json
from ..autodoc.request import URLPath
from ..autodoc.schema import String
from . import simple_routing

logger = logging.getLogger(__name__)


class SimpleRoutingRoute:
    _di = None
    _handler = None
    _methods = None
    _path = None
    _path_parts = None
    _resource_paths = None
    _routes_to_simple_routing = False
    _bindings = None
    _path_parameter_with_slashes = None
    _has_sub_paths = None

    def __init__(self, di):
        self._di = di

    def configure(
        self,
        handler_class,
        handler_config,
        path=None,
        methods=None,
        authentication=None,
        response_headers=None,
        security_headers=None,
        path_parameter_with_slashes=None,
        bindings=None,
        has_sub_paths=True,
    ):
        if authentication is not None and not handler_config.get("authentication"):
            handler_config["authentication"] = authentication
        response_headers = response_headers if response_headers is not None else {}
        if "response_headers" in handler_config:
            if type(handler_config["response_headers"]) != dict:
                raise ValueError("Invalid configuration: 'response_headers' must be a dictionary")
            response_headers = {**response_headers, **handler_config["response_headers"]}
        self._path = path
        if handler_config.get("base_url"):
            self._path = path.rstrip("/") + "/" + handler_config.get("base_url").lstrip("/")
        self._path_parts = self._path.strip("/").split("/") if self._path is not None else []
        self._resource_paths = self._extract_resource_paths(self._path_parts)
        self._bindings = bindings if bindings else {}
        self._path_parameter_with_slashes = path_parameter_with_slashes if path_parameter_with_slashes else []
        self._has_sub_paths = has_sub_paths
        if methods is not None:
            self._methods = [methods.upper()] if isinstance(methods, str) else [met.upper() for met in methods]
        sub_handler_config = {
            **handler_config,
            **{
                "base_url": ("/" + path.strip("/")) if path is not None else "/",
            },
        }
        if response_headers:
            sub_handler_config["response_headers"] = response_headers
        security_headers = security_headers if security_headers is not None else []
        if "security_headers" in handler_config:
            security_headers = [*security_headers, *handler_config["security_headers"]]
        sub_handler_config["security_headers"] = security_headers
        self._handler = self._di.build(handler_class, cache=False)
        self._handler.configure(sub_handler_config)
        self._routes_to_simple_routing = issubclass(handler_class, simple_routing.SimpleRouting)

    def _extract_resource_paths(self, path_parts):
        resource_paths = {}
        for index, part in enumerate(path_parts):
            if not part:
                continue
            if part[0] != "{":
                continue
            if part[-1] != "}":
                raise ValueError(
                    f"Invalid route configuration for URL '{path}': section '{part}'"
                    + " starts with a '{' but does not end with one"
                )
            match = re.match("{(\\w[\\w\\d_]{0,})\\}", part)
            if not match:
                raise ValueError(
                    f"Invalid route configuration for URL '{path}', section '{part}': resource identifiers must start with a letter and contain only letters, numbers, and underscores"
                )
            resource_paths[index] = match.group(1)
        return resource_paths

    def matches(self, full_path, request_method, is_cors=False):
        """Returns None if the route doesn't match, or a dictionary with route data for a match.

        You can't just match true/false against the return value, because of the route matches
        but has no route data, it returns an empty dictionary.  Check explicitly for None
        to understand if there was no route match at all.
        """
        # if we're routing to a simple router then defer to it
        incoming = f"Incoming request: [{request_method}] {full_path}.  Check against route with url '{self._path}'.  Results: "
        if not self._methods:
            incoming += " configured for any method except OPTIONS"
        elif isinstance(self._methods, str):
            incoming += f" with method '{self._methods}'"
        else:
            incoming += " with any of the following methods: " + ", ".join(self._methods)
        if self._routes_to_simple_routing:
            return self._handler.can_handle(full_path, request_method, is_cors=is_cors)
        # If we're routing for CORS then ignore the request method (since it won't match)
        if not is_cors and self._methods is not None and request_method not in self._methods:
            logger.debug(
                f"{incoming} Skipped because this route is not specifically configured for CORS, and this is an OPTIONS request."
            )
            return None
        if self._resource_paths:
            results = self._resource_path_match(full_path, self._path_parts, self._resource_paths)
            if not results:
                logger.debug(f"{incoming} Not a match.")
            else:
                logger.debug(f"{incoming} Matched and extracted route data: " + json.dumps(results))
            return results
        if self._path is not None:
            full_path = full_path.strip("/")
            my_path = self._path.strip("/")
            my_path_length = len(my_path)
            full_path_length = len(full_path)
            if my_path_length > full_path_length:
                logger.debug(f"{incoming} Not a match. I'm too long to bother checking.")
                return None
            if full_path[:my_path_length] != my_path:
                logger.debug(f"{incoming} Not a match.  Our prefixes just don't match.")
                return None
            if not self._has_sub_paths and full_path_length > my_path_length:
                logger.debug(f"{incoming} Not a match.  It's a partial match but I'm not allowed to do that.")
                return None
            # make sure we don't get confused by partial matches.  `user` should match `user/` and `user/5`,
            # but it shouldn't match `users/`
            if full_path_length > my_path_length and full_path[my_path_length] != "/" and my_path != "":
                logger.debug(f"{incoming} Not a match.  I only partially matched the URL but not as a sub-directory.")
                return None
        logger.debug(f"{incoming} Match!")
        return {}

    def _resource_path_match(self, requested_path, path_parts, resource_paths):
        """Returns None if the route doesn't match, or a dictionary with route data for the match."""
        requested_parts = requested_path.strip("/").split("/")
        route_data = {}
        path_length = len(path_parts)
        # it's okay if the requested path is longer than the configured path, since there may
        # be sub-routes that we don't know about.  However, we won't ever have a match if
        # the requested path is shorter than the configured path.
        if len(requested_parts) < path_length:
            return None
        for index in range(path_length):
            if index in resource_paths:
                if resource_paths[index] in self._path_parameter_with_slashes:
                    route_data[resource_paths[index]] = urllib.parse.unquote("/".join(requested_parts[index:]))
                else:
                    route_data[resource_paths[index]] = urllib.parse.unquote(requested_parts[index])
            else:
                if requested_parts[index] != path_parts[index]:
                    return None
        return route_data

    def __call__(self, input_output):
        # including calling parameters that came from the route matching
        return self._handler(input_output)

    def cors(self, input_output):
        # including calling parameters that came from the route matching
        return self._handler.cors(input_output)

    def documentation(self):
        docs = []
        for doc in self._handler.documentation():
            if self._methods is not None:
                doc.set_request_methods(self._methods)

            # do we have any resource paths to document?
            for path_name in self._resource_paths.values():
                description = f"The {path_name} to show results for"
                doc.add_parameter(URLPath(String(path_name), description=description, required=True))

            docs.append(doc)
        return docs

    def documentation_models(self):
        return self._handler.documentation_models()

    def documentation_security_schemes(self):
        return self._handler.documentation_security_schemes()
