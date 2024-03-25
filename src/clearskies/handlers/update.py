from .write import Write
from .exceptions import InputError
from collections import OrderedDict
from ..functional import string


class Update(Write):
    def __init__(self, di):
        super().__init__(di)

    _configuration_defaults = {
        "model": None,
        "model_class": None,
        "columns": None,
        "column_overrides": None,
        "writeable_columns": None,
        "readable_columns": None,
        "output_map": None,
        "where": [],
        "input_error_callable": None,
        "include_id_in_path": False,
    }

    def get_model_id(self, input_output, input_data):
        routing_data = input_output.routing_data()
        if self.id_column_name in routing_data:
            return routing_data[self.id_column_name]
        if "id" in routing_data:
            return routing_data["id"]
        raise ValueError("I didn't receive the ID in my routing data.  I am probably misconfigured.")

    def handle(self, input_output):
        input_data = self.request_data(input_output)
        model_id = self.get_model_id(input_output, input_data)
        if not model_id:
            return self.error(input_output, "Not Found", 404)
        id_column_name = self.id_column_name
        models = self._model.where(f"{id_column_name}={model_id}")
        for where in self.configuration("where"):
            if type(where) == str:
                models = models.where(where)
            else:
                models = self._di.call_function(
                    where, models=models, input_output=input_output, routing_data=input_output.routing_data()
                )
        models = models.where_for_request(
            models,
            input_output.routing_data(),
            input_output.get_authorization_data(),
            input_output,
            overrides=self.configuration("column_overrides"),
        )
        authorization = self._configuration.get("authorization", None)
        if authorization and hasattr(authorization, "filter_models"):
            models = authorization.filter_models(models, input_output.get_authorization_data(), input_output)
        model = models.first()
        if not model.exists:
            return self.error(input_output, "Not Found", 404)
        if "id" in input_data:
            del input_data["id"]

        input_errors = {
            **self._extra_column_errors(input_data),
            **self._find_input_errors(model, input_data, input_output),
        }
        if input_errors:
            raise InputError(input_errors)
        model.save(input_data, columns=self._get_writeable_columns())

        return self.success(input_output, self._model_as_json(model, input_output))

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)
        error_prefix = "Configuration error for %s:" % (self.__class__.__name__)
        if "where" in configuration:
            if not hasattr(configuration["where"], "__iter__") or type(configuration["where"]) == str:
                raise ValueError(
                    f"{error_prefix} 'where' should be an iterable of coditions or callables "
                    + ", not "
                    + str(type(configuration["where"])),
                )
            for index, where in enumerate(configuration["where"]):
                if type(where) != str and not callable(where):
                    raise ValueError(
                        f"{error_prefix} 'where' entry should be a string with a condition or a callable that filters models "
                        + f", but entry #{index+1} is neither of these",
                    )

    def documentation(self):
        nice_model = string.camel_case_to_words(self._model.__class__.__name__)
        id_label = "id" if self.configuration("id_column_name") else self.id_column_name
        return self._documentation(
            description="Update the " + nice_model + " with an " + id_label + " of {" + id_label + "}",
            response_description=f"The updated {nice_model}",
            include_id_in_path=self.configuration("include_id_in_path"),
        )
