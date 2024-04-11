from abc import ABC, abstractmethod
from . import exceptions
from collections import OrderedDict
import inspect
import re
from ..autodoc.schema import Integer as AutoDocInteger
from ..autodoc.schema import String as AutoDocString
from ..autodoc.schema import Object as AutoDocObject
from ..autodoc.response import Response as AutoDocResponse
from ..functional import string
from typing import List, Dict


class Base(ABC):
    _configuration = None
    _configuration_defaults = {}
    _as_json_map = None
    _global_configuration_defaults = {
        "base_url": "",
        "response_headers": None,
        "authentication": None,
        "authorization": None,
        "output_map": None,
        "column_overrides": None,
        "id_column_name": None,
        "doc_description": "",
        "internal_casing": "",
        "external_casing": "",
        "security_headers": None,
    }
    _di = None
    _configuration = None
    _cors_header = None
    has_cors = False

    def __init__(self, di):
        self._di = di
        self._configuration = None

    @abstractmethod
    def handle(self):
        pass

    def configure(self, configuration):
        for key in configuration.keys():
            if key not in self._configuration_defaults and key not in self._global_configuration_defaults:
                class_name = self.__class__.__name__
                raise KeyError(f"Attempt to set unknown configuration setting '{key}' for handler '{class_name}'")

        self._check_configuration(configuration)
        self._configuration = self._finalize_configuration(self.apply_default_configuration(configuration))

    def _check_configuration(self, configuration):
        if not "authentication" in configuration:
            raise KeyError(
                f"You must provide authentication in the configuration for handler '{self.__class__.__name__}'"
            )
        if configuration.get("authorization", None):
            # authorization can be a function (in which case we'll just call it for gating) or it can be an object
            # with 'gate' and 'filter_models' attributes, per the authentication.authorization base class
            # or it can be a binding config
            authorization = configuration["authorization"]
            if type(authorization) == str:
                # if we have a binding name then we need to build the authorization object
                authorization = self._di.build(authorization, cache=True)
            elif hasattr(authorization, "object_class"):
                # if it's a binding config then pull out the target class, since we just need to check attributes here
                authorization = authorization.object_class
            is_callable = callable(authorization)
            gates_or_filters = hasattr(authorization, "gate") or hasattr(authorization, "filter_models")
            if not is_callable and not gates_or_filters:
                raise ValueError("'authorization' should be a callable or a provide 'gate' or 'filter_models' methods")
        if configuration.get("output_map") is not None:
            if not callable(configuration["output_map"]):
                raise ValueError("'output_map' should be a callable")
        number_casings = 0
        internal_casing = configuration.get("internal_casing")
        if internal_casing and internal_casing not in string.casings:
            raise ValueError(
                f"Invalid internal_casing config for handler '{self.__class__.__name__}': expected one of "
                + "'"
                + ", '".join(string.casings)
                + f"' but found '{internal_casing}'"
            )
            number_casings += 1
        external_casing = configuration.get("external_casing")
        if external_casing and external_casing not in string.casings:
            raise ValueError(
                f"Invalid external_casing config for handler '{self.__class__.__name__}': expected one of "
                + "'"
                + ", '".join(string.casings)
                + f"' but found '{external_casing}'"
            )
            number_casings += 1
        if number_casings == 1:
            raise ValueError(
                f"Configuration error for handler '{self.__class__.__name__}': external_casing and internal_casing"
                + " must be specified together, but only one was found"
            )
        if "base_url" in configuration and configuration["base_url"] != None and type(configuration["base_url"]) != str:
            raise ValueError(
                f"Configuration error for handler '{self.__class__.__name__}': if provided, base_url must be a string"
            )

    def apply_default_configuration(self, configuration):
        return {
            **self._global_configuration_defaults,
            **self._configuration_defaults,
            **configuration,
        }

    def configuration(self, key):
        if self._configuration is None:
            raise ValueError("Cannot fetch configuration values before setting the configuration")
        if key not in self._configuration:
            class_name = self.__class__.__name__
            raise KeyError(f"Configuration key '{key}' does not exist for handler '{class_name}'")
        return self._configuration[key]

    def _finalize_configuration(self, configuration):
        configuration["authentication"] = self._di.build(configuration["authentication"], cache=True)
        authorization = configuration.get("authorization")
        if authorization and (hasattr(authorization, "object_class") or type(authorization) == str):
            configuration["authorization"] = self._di.build(configuration["authorization"], cache=True)
        if configuration.get("base_url") is None:
            configuration["base_url"] = "/"
        if not configuration["base_url"] or configuration["base_url"][0] != "/":
            configuration["base_url"] = "/" + configuration["base_url"]
        security_headers = configuration.get("security_headers")
        if not security_headers:
            configuration["security_headers"] = []
        else:
            # should be a list or a binding config.  If it's a binding config, convert it to a list
            if hasattr(security_headers, "object_class"):
                security_headers = [security_headers]
            if type(security_headers) != list:
                raise ValueError(
                    f"Configuration error for handler '{self.__class__.__name__}': if provided, security_headers must be a list or binding config"
                )
            final_security_headers = []
            for index, security_header in enumerate(security_headers):
                if hasattr(security_header, "object_class"):
                    security_header = self._di.build(security_header, cache=True)
                if not hasattr(security_header, "set_headers_for_input_output"):
                    raise ValueError(
                        f"Configuration error for handler '{self.__class__.__name__}': security header #{index+1} did not resolve to a security header"
                    )
                if security_header.is_cors:
                    self._cors_header = security_header
                    self.has_cors = True
                final_security_headers.append(security_header)
            configuration["security_headers"] = final_security_headers
        return configuration

    def top_level_authentication_and_authorization(self, input_output, authentication=None):
        if authentication is None:
            authentication = self._configuration.get("authentication")
        if not authentication:
            return
        try:
            if not authentication.authenticate(input_output):
                raise exceptions.Authentication("Not Authenticated")
        except exceptions.ClientError as client_error:
            raise exceptions.Authentication(str(client_error))
        authorization = self._configuration.get("authorization")
        if authorization:
            authorization_data = input_output.get_authorization_data()
            try:
                allowed = True
                if hasattr(authorization, "gate"):
                    allowed = authorization.gate(authorization_data, input_output)
                elif callable(authorization):
                    allowed = authorization(authorization_data, input_output)
                if not allowed:
                    raise exceptions.Authorization("Not Authorized")
            except exceptions.ClientError as client_error:
                raise exception.Authorization(str(client_error))

    def __call__(self, input_output):
        self._di.bind("input_output", input_output)
        if self._configuration is None:
            raise ValueError("Must configure handler before calling")
        try:
            self.top_level_authentication_and_authorization(input_output)
        except exceptions.Authentication as auth_error:
            return self.error(input_output, str(auth_error), 401)
        except exceptions.Authorization as auth_error:
            return self.error(input_output, str(auth_error), 403)
        except exceptions.NotFound as auth_error:
            return self.error(input_output, str(auth_error), 404)

        try:
            response = self.handle(input_output)
        except exceptions.ClientError as client_error:
            return self.error(input_output, str(client_error), 400)
        except exceptions.InputError as input_error:
            return self.input_errors(input_output, input_error.errors)
        except exceptions.Authentication as auth_error:
            return self.error(input_output, str(auth_error), 401)
        except exceptions.Authorization as auth_error:
            return self.error(input_output, str(auth_error), 403)
        except exceptions.NotFound as auth_error:
            return self.error(input_output, str(auth_error), 404)

        return response

    def input_errors(self, input_output, errors, status_code=200):
        return self.respond(input_output, {"status": "input_errors", "input_errors": errors}, status_code)

    def error(self, input_output, message, status_code):
        return self.respond(input_output, {"status": "client_error", "error": message}, status_code)

    def success(self, input_output, data, number_results=None, limit=None, next_page=None):
        response_data = {"status": "success", "data": data, "pagination": {}}

        if number_results is not None:
            for value in [number_results, limit]:
                if value is not None and type(value) != int:
                    raise ValueError("number_results and limit must all be integers")

            response_data["pagination"] = {
                "number_results": number_results,
                "limit": limit,
                "next_page": next_page,
            }

        return self.respond(input_output, response_data, 200)

    def respond(self, input_output, response_data, status_code):
        response_headers = self.configuration("response_headers")
        if response_headers:
            input_output.set_headers(response_headers)
        for security_header in self.configuration("security_headers"):
            security_header.set_headers_for_input_output(input_output)
        return input_output.respond(self._normalize_response(response_data), status_code)

    def _normalize_response(self, response_data):
        if not "status" in response_data:
            raise ValueError("Huh, status got left out somehow")
        return {
            self.auto_case_internal_column_name("status"): self.auto_case_internal_column_name(response_data["status"]),
            self.auto_case_internal_column_name("error"): response_data.get("error", ""),
            self.auto_case_internal_column_name("data"): response_data.get("data", []),
            self.auto_case_internal_column_name("pagination"): self._normalize_pagination(
                response_data.get("pagination", {})
            ),
            self.auto_case_internal_column_name("input_errors"): response_data.get("input_errors", {}),
        }

    def _normalize_pagination(self, pagination):
        # pagination isn't always relevant so if it is completely empty then leave it that way
        if not pagination:
            return pagination
        return {
            self.auto_case_internal_column_name("number_results"): pagination.get("number_results", 0),
            self.auto_case_internal_column_name("limit"): pagination.get("limit", 0),
            self.auto_case_internal_column_name("next_page"): {
                self.auto_case_internal_column_name(key): value
                for (key, value) in pagination.get("next_page", {}).items()
            },
        }

    def _model_as_json(self, model, input_output):
        if self.configuration("output_map"):
            return self._di.call_function(self.configuration("output_map"), model=model)

        if self._as_json_map is None:
            self._as_json_map = self._build_as_json_map(model)

        json = OrderedDict()
        for output_name, column in self._as_json_map.items():
            column_data = column.to_json(model)
            if len(column_data) == 1:
                json[output_name] = list(column_data.values())[0]
            else:
                for key, value in column_data.items():
                    json[self.auto_case_column_name(key, True)] = value
        return json

    def _build_as_json_map(self, model):
        conversion_map = {}
        if self.configuration("id_column_name"):
            conversion_map[self.auto_case_internal_column_name("id")] = model.columns()[self.id_column_name]

        for column in self._get_readable_columns().values():
            conversion_map[self.auto_case_column_name(column.name, True)] = column
        return conversion_map

    def auto_case_internal_column_name(self, column_name):
        if self._configuration["external_casing"]:
            return string.swap_casing(column_name, "snake_case", self._configuration["external_casing"])
        return column_name

    def auto_case_to_internal_column_name(self, column_name):
        if self._configuration["external_casing"]:
            return string.swap_casing(column_name, self._configuration["external_casing"], "snake_case")
        return column_name

    def auto_case_column_name(self, column_name, internal_to_external):
        if not self._configuration["internal_casing"]:
            return column_name
        if internal_to_external:
            return string.swap_casing(
                column_name,
                self._configuration["internal_casing"],
                self._configuration["external_casing"],
            )
        return string.swap_casing(
            column_name,
            self._configuration["external_casing"],
            self._configuration["internal_casing"],
        )

    @property
    def id_column_name(self) -> str:
        """
        This returns the name of the id column to use for requests

        There are three ways to determine the id column:

         1. It may be defined in the handler configuration.
         2. It may be overridden in the model class
         3. It defaults to 'id'

        The first happens if the developer wants to expose a different "id" column to the client.
        The second happens if the developer wants to use a different id column internally.
        The third is the clearskies default.

        The first is easy to detect because the dev will set `id_column_name` in the handler config.
        The second happens if the model class defines a different `id_column_name` property in the model class.
        However, this is tricky because there is nothing in this base case that allows us to pull up the model.
        In fact, not all handlers use a model, or they may use multiple models, etc...  Still, it's pretty
        common for the handler to have a configuration named `model_class` or `model`, so let's check for that and assume
        the handler will only ask for the id_column_name() if the handler has a `self.configuration('model_class')`
        """
        id_column_name = self.configuration("id_column_name")
        if id_column_name is not None:
            return id_column_name
        if not self._configuration.get("model_class", False) and not self._configuration.get("model", False):
            raise KeyError(
                "To properly use handler.id_column_name, the handler must have a 'model_class' or 'model' configuration key"
            )
        if self._configuration.get("model_class", False):
            return self._configuration.get("model_class").id_column_name
        return self._configuration.get("model").id_column_name

    def cors(self, input_output):
        cors = self._cors_header
        if not cors:
            return self.error(input_output, "not found", 404)
        authentication = self._configuration.get("authentication")
        if authentication:
            authentication.set_headers_for_cors(cors)
        cors.set_headers_for_input_output(input_output)
        return input_output.respond("", 200)

    def documentation(self):
        return []

    def documentation_components(self):
        return {
            "models": self.documentation_models(),
            "securitySchemes": self.documentation_security_schemes(),
        }

    def documentation_security_schemes(self):
        authentication = self._configuration.get("authentication")
        if not authentication or not authentication.documentation_security_scheme_name():
            return {}

        return {
            authentication.documentation_security_scheme_name(): authentication.documentation_security_scheme(),
        }

    def documentation_models(self):
        return {}

    def documentation_pagination_response(self, include_pagination=True):
        if not include_pagination:
            return AutoDocObject(self.auto_case_internal_column_name("pagination"), [], value={})
        return AutoDocObject(
            self.auto_case_internal_column_name("pagination"),
            [
                AutoDocInteger(self.auto_case_internal_column_name("number_results"), example=10),
                AutoDocInteger(self.auto_case_internal_column_name("limit"), example=100),
                AutoDocObject(
                    self.auto_case_internal_column_name("next_page"),
                    self._model.documentation_pagination_next_page_response(self.auto_case_internal_column_name),
                    self._model.documentation_pagination_next_page_example(self.auto_case_internal_column_name),
                ),
            ],
        )

    def documentation_success_response(self, data_schema, description="", include_pagination=False):
        return AutoDocResponse(
            200,
            AutoDocObject(
                "body",
                [
                    AutoDocString(self.auto_case_internal_column_name("status"), value="success"),
                    data_schema,
                    self.documentation_pagination_response(include_pagination=include_pagination),
                    AutoDocString(self.auto_case_internal_column_name("error"), value=""),
                    AutoDocObject(self.auto_case_internal_column_name("input_errors"), [], value={}),
                ],
            ),
            description=description,
        )

    def documentation_generic_error_response(self, description="Invalid Call", status=400):
        return AutoDocResponse(
            status,
            AutoDocObject(
                "body",
                [
                    AutoDocString(self.auto_case_internal_column_name("status"), value="error"),
                    AutoDocObject(self.auto_case_internal_column_name("data"), [], value={}),
                    self.documentation_pagination_response(include_pagination=False),
                    AutoDocString(self.auto_case_internal_column_name("error"), example="User readable error message"),
                    AutoDocObject(self.auto_case_internal_column_name("input_errors"), [], value={}),
                ],
            ),
            description=description,
        )

    def documentation_input_error_response(self, description="Invalid client-side input"):
        email_example = self.auto_case_internal_column_name("email")
        return AutoDocResponse(
            200,
            AutoDocObject(
                "body",
                [
                    AutoDocString(self.auto_case_internal_column_name("status"), value="input_errors"),
                    AutoDocObject(self.auto_case_internal_column_name("data"), [], value={}),
                    self.documentation_pagination_response(include_pagination=False),
                    AutoDocString(self.auto_case_internal_column_name("error"), value=""),
                    AutoDocObject(
                        self.auto_case_internal_column_name("input_errors"),
                        [AutoDocString("[COLUMN_NAME]", example="User friendly error message")],
                        example={email_example: f"{email_example} was not a valid email address"},
                    ),
                ],
            ),
            description=description,
        )

    def documentation_access_denied_response(self):
        return self.documentation_generic_error_response(description="Access Denied", status=401)

    def documentation_unauthorized_response(self):
        return self.documentation_generic_error_response(description="Unauthorized", status=403)

    def documentation_not_found(self):
        return self.documentation_generic_error_response(description="Not Found", status=404)

    def documentation_request_security(self):
        authentication = self.configuration("authentication")
        name = authentication.documentation_security_scheme_name()
        return [{name: []}] if name else []

    def documentation_data_schema(self):
        id_column_name = self.id_column_name
        properties = []
        if self.configuration("id_column_name"):
            properties.append(
                self._columns[id_column_name].documentation(name=self.auto_case_internal_column_name("id"))
                if id_column_name in self._columns
                else AutoDocString(self.auto_case_internal_column_name("id"))
            )

        for column in self._get_readable_columns().values():
            column_doc = column.documentation()
            if type(column_doc) != list:
                column_doc = [column_doc]
            for doc in column_doc:
                doc.name = self.auto_case_internal_column_name(doc.name)
                properties.append(doc)

        return properties
