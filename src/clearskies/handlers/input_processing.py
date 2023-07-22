from .exceptions import InputError
from collections import OrderedDict
from abc import abstractmethod


class InputProcessing:
    _is_create = False

    def _get_writeable_columns(self):
        if self._writeable_columns is None:
            self._writeable_columns = self._get_rw_columns("writeable")
            additional_columns = OrderedDict()
            for column in self._writeable_columns.values():
                more_columns = column.additional_write_columns(is_create=self._is_create)
                for additional_column_name, additional_column in more_columns.items():
                    additional_columns[additional_column_name] = additional_column
            for additional_column_name, additional_column in additional_columns.items():
                self._writeable_columns[additional_column_name] = additional_column
        return self._writeable_columns

    def _extra_column_errors(self, input_data):
        input_errors = {}
        allowed = self._get_writeable_columns()
        for column_name in input_data.keys():
            if column_name not in allowed:
                input_errors[column_name] = f"Input column '{column_name}' is not an allowed column"
        return input_errors

    def _find_input_errors(self, model, input_data, input_output):
        input_errors = {}
        for column in self._get_writeable_columns().values():
            input_errors = {
                **input_errors,
                **column.input_errors(model, input_data),
            }
        input_error_callable = self.configuration("input_error_callable")
        if input_error_callable:
            more_input_errors = self._di.call_function(
                input_error_callable,
                input_data=input_data,
                request_data=input_data,
                input_output=input_output,
                routing_data=input_output.routing_data(),
                authorization_data=input_output.get_authorization_data(),
            )
            if type(more_input_errors) != dict:
                raise ValueError(
                    "The input error callable, '"
                    + str(input_error_callable)
                    + "', did not return a dictionary as required"
                )
            input_errors = {
                **input_errors,
                **more_input_errors,
            }
        return input_errors

    def request_data(self, input_output, required=True):
        # we have to map from internal names to external names, because case mapping
        # isn't always one-to-one, so we want to do it exactly the same way that the documentation
        # is built.
        key_map = {self.auto_case_column_name(key, True): key for key in self._get_writeable_columns().keys()}
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
