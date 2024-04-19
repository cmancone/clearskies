from .base import Base
from .schema_helper import SchemaHelper
from .exceptions import InputError, ClientError, NotFound
import inspect
import json
from ..functional import validations, string
from .. import autodoc


class Callable(Base, SchemaHelper):
    _columns = None

    _global_configuration_defaults = {
        "response_headers": None,
        "authentication": None,
        "authorization": None,
        "callable": None,
        "id_column_name": None,
        "doc_description": "",
        "internal_casing": "",
        "external_casing": "",
        "security_headers": None,
    }

    _configuration_defaults = {
        "base_url": "",
        "return_raw_response": False,
        "schema": None,
        "writeable_columns": None,
        "doc_model_name": "",
        "doc_response_data_schema": None,
    }

    def __init__(self, di):
        super().__init__(di)

    def handle(self, input_output):
        self._di.bind("input_output", input_output)
        try:
            if self.configuration("schema"):
                request_data = self.request_data(input_output)
                input_errors = {
                    **self._extra_column_errors(request_data),
                    **self._find_input_errors(request_data),
                }
                if input_errors:
                    return self.input_errors(input_output, input_errors)
                response = self._di.call_function(
                    self.configuration("callable"),
                    **input_output.routing_data(),
                    **input_output.context_specifics(),
                    request_data=request_data,
                    authorization_data=input_output.get_authorization_data(),
                )
            else:
                response = self._di.call_function(
                    self.configuration("callable"),
                    **input_output.routing_data(),
                    **input_output.context_specifics(),
                    request_data=self.request_data(input_output, required=False),
                    authorization_data=input_output.get_authorization_data(),
                )
            if response:
                return self.success(input_output, response)
            return
        except InputError as e:
            if e.errors:
                return self.input_errors(input_output, e.errors)
            else:
                return self.input_errors(input_output, str(e))
        except ClientError as e:
            return self.error(input_output, str(e), 400)
        except NotFound as e:
            return self.error(input_output, str(e), 404)

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)
        error_prefix = "Configuration error for %s:" % (self.__class__.__name__)
        if not "callable" in configuration:
            raise KeyError(f"{error_prefix} you must specify 'callable'")
        if not callable(configuration["callable"]):
            raise ValueError(f"{error_prefix} the provided callable is not actually callable")
        if configuration.get("schema") is not None:
            self._check_schema(configuration["schema"], configuration.get("writeable_columns"), error_prefix)

    def _finalize_configuration(self, configuration):
        configuration = super()._finalize_configuration(configuration)
        if configuration.get("schema") is not None:
            if validations.is_model(configuration["schema"]):
                configuration["doc_model_name"] = configuration["schema"].__class__.__name__
            elif validations.is_model_class(configuration["schema"]):
                configuration["doc_model_name"] = configuration["schema"].__name__
            configuration["schema"] = self._schema_to_columns(
                configuration["schema"], columns_to_keep=configuration.get("writeable_columns")
            )
        return configuration

    def request_data(self, input_output, required=True):
        if not self.configuration("schema"):
            return input_output.request_data(required=required)
        # we have to map from internal names to external names, because case mapping
        # isn't always one-to-one, so we want to do it exactly the same way that the documentation
        # is built.
        key_map = {self.auto_case_column_name(key, True): key for key in self.configuration("schema").keys()}
        # in case the id comes up in the request body
        key_map[self.auto_case_internal_column_name("id")] = "id"

        # and make sure we don't drop any data along the way, because the input validation
        # needs to return an error for unexpected data.
        request_data = {
            key_map.get(key, key): value for (key, value) in input_output.request_data(required=required).items()
        }
        # the parent handler should provide our resource id (we don't do any routing ourselves)
        # However, our update/etc handlers need to find the id easily, so I'm going to be lazy and
        # just dump it into the request.  I'll probably regret that.
        routing_data = input_output.routing_data()
        # we don't have to worry about casing on the 'id' in routing_data because it doesn't come in from the
        # route with a name.  Rather, it is populated by clearskies, so will always just be 'id'
        if "id" in routing_data:
            request_data["id"] = routing_data["id"]
        return request_data

    def success(self, input_output, data, number_results=None, limit=None, next_page=None):
        if self.configuration("return_raw_response"):
            return input_output.respond(data, 200)

        return super().success(input_output, data, number_results=number_results, limit=limit, next_page=next_page)

    def documentation(self):
        schema = self.configuration("schema")

        # our request parameters
        parameters = []
        if schema:
            parameters = [
                autodoc.request.JSONBody(
                    column.documentation(name=self.auto_case_column_name(column.name, True)),
                    description=f"Set '{column.name}'",
                    required=column.is_required,
                )
                for column in schema.values()
            ]

        authentication = self.configuration("authentication")
        standard_error_responses = []
        if not getattr(authentication, "is_public", False):
            standard_error_responses.append(self.documentation_access_denied_response())
            if getattr(authentication, "can_authorize", False):
                standard_error_responses.append(self.documentation_unauthorized_response())

        response_data_schema = self.configuration("doc_response_data_schema")
        if not response_data_schema:
            response_data_schema = []

        return [
            autodoc.request.Request(
                self.configuration("doc_description"),
                [
                    self.documentation_success_response(
                        autodoc.schema.Object(
                            self.auto_case_internal_column_name("data"),
                            children=response_data_schema,
                            model_name=self.configuration("doc_model_name"),
                        ),
                        include_pagination=False,
                    ),
                    *standard_error_responses,
                    self.documentation_not_found(),
                ],
                request_methods="POST" if schema else "GET",
                relative_path=self.configuration("base_url"),
                parameters=[
                    *parameters,
                ],
                root_properties={
                    "security": self.documentation_request_security(),
                },
            )
        ]

    def documentation_models(self):
        if not self.configuration("doc_model_name") or not self.configuration("doc_response_data_schema"):
            return {}

        schema_model_name = self.configuration("doc_model_name")
        return {
            schema_model_name: autodoc.schema.Object(
                "data",
                children=self.configuration("doc_response_data_schema"),
            ),
        }
