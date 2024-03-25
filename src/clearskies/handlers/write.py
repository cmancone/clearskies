from .base import Base
from .input_processing import InputProcessing
from .exceptions import InputError
from collections import OrderedDict
from abc import abstractmethod
from .. import autodoc
from ..functional import string
import inspect


class Write(Base, InputProcessing):
    _di = None
    _model = None
    _columns = None
    _authentication = None
    _writeable_columns = None
    _readable_columns = None

    _configuration_defaults = {
        "model": None,
        "model_class": None,
        "columns": None,
        "column_overrides": None,
        "writeable_columns": None,
        "output_map": None,
        "readable_columns": None,
        "input_error_callable": None,
    }

    def __init__(self, di):
        super().__init__(di)

    @abstractmethod
    def handle(self, input_output):
        pass

    def _check_configuration(self, configuration):
        super()._check_configuration(configuration)
        error_prefix = "Configuration error for %s:" % (self.__class__.__name__)
        has_model_class = ("model_class" in configuration) and configuration["model_class"] is not None
        has_model = ("model" in configuration) and configuration["model"] is not None
        if not has_model and not has_model_class:
            raise KeyError(f"{error_prefix} you must specify 'model' or 'model_class'")
        if has_model and has_model_class:
            raise KeyError(f"{error_prefix} you specified both 'model' and 'model_class', but can only provide one")
        if has_model and inspect.isclass(configuration["model"]):
            raise ValueError(
                "{error_prefix} you must provide a model instance in the 'model' configuration setting, but a class was provided instead"
            )
        if "input_error_callable" in configuration and not callable(configuration.get("input_error_callable")):
            raise ValueError(
                "{error_prefix} you must provide a callable for the 'input_error_callable' configuration but the provided value is not callable"
            )
        self._model = self._di.build(configuration["model_class"]) if has_model_class else configuration["model"]
        self._columns = self._model.columns(overrides=configuration.get("column_overrides"))
        has_columns = "columns" in configuration and configuration["columns"] is not None
        has_writeable = "writeable_columns" in configuration and configuration["writeable_columns"] is not None
        has_readable = "readable_columns" in configuration and configuration["readable_columns"] is not None
        if not has_columns and not has_writeable:
            raise KeyError(f"{error_prefix} you must specify 'columns' OR 'writeable_columns'")
        if not has_columns and not has_readable:
            raise KeyError(f"{error_prefix} you must specify 'columns' OR 'readable_columns'")
        if has_columns and has_writeable:
            raise KeyError(f"{error_prefix} you must specify 'columns' OR 'writeable_columns', not both")
        if has_columns and has_readable:
            raise KeyError(f"{error_prefix} you must specify 'columns' OR 'readable_columns', not both")
        if has_writeable and not has_readable:
            raise KeyError(f"{error_prefix} you must specify 'readable_columns' if you specify 'writeable_columns'")
        if has_readable and not has_writeable:
            raise KeyError(f"{error_prefix} you must specify 'writeable_columns' if you specify 'readable_columns'")

        for config_name in ["columns", "writeable_columns", "readable_columns"]:
            if config_name not in configuration or configuration[config_name] is not None:
                continue
            if hasattr(configuration[config_name], "__iter__"):
                continue
            raise ValueError(
                f"{error_prefix} '{config_name}' should be a list of column names "
                + f", not {str(type(configuration[config_name]))}"
            )

        if has_columns and not configuration["columns"]:
            raise KeyError(f"{error_prefix} you must specify at least one column for 'columns'")
        if has_writeable and not configuration["writeable_columns"]:
            raise KeyError(f"{error_prefix} you must specify at least one column for 'writeable_columns'")
        if has_readable and not configuration["readable_columns"]:
            raise KeyError(f"{error_prefix} you must specify at least one column for 'readable_columns'")
        writeable_columns = configuration["writeable_columns"] if has_writeable else configuration["columns"]
        for column_name in writeable_columns:
            if column_name not in self._columns:
                raise KeyError(f"{error_prefix} specified writeable column '{column_name}' does not exist")
            if not self._columns[column_name].is_writeable:
                raise KeyError(f"{error_prefix} specified writeable column '{column_name}' is not writeable")
        readable_columns = configuration["readable_columns"] if has_readable else configuration["columns"]
        for column_name in readable_columns:
            if column_name not in self._columns:
                raise KeyError(f"{error_prefix} specified readable column '{column_name}' does not exist")

    def _get_rw_columns(self, rw_type):
        column_names = self.configuration("columns")
        if column_names is None:
            column_names = self.configuration(f"{rw_type}_columns")
        wr_columns = OrderedDict()
        for column_name in column_names:
            if column_name not in self._columns:
                class_name = self.__class__.__name__
                model_class = self._model.__class__.__name__
                raise ValueError(
                    f"Configuration error for {self.__class__.__name__}: handler was configured with {rw_type} "
                    + f"column '{column_name}' but this column doesn't exist for model {model_class}"
                )
            wr_columns[column_name] = self._columns[column_name]
        return wr_columns

    def _get_readable_columns(self):
        if self._readable_columns is None:
            self._readable_columns = self._get_rw_columns("readable")
        return self._readable_columns

    def documentation_models(self):
        schema_model_name = string.camel_case_to_snake_case(self._model.__class__.__name__)

        return {
            schema_model_name: autodoc.schema.Object(
                "data",
                children=self.documentation_data_schema(),
            ),
        }

    def _documentation(self, description="", response_description="", include_id_in_path=False):
        nice_model = string.camel_case_to_words(self._model.__class__.__name__)
        data_schema = self.documentation_data_schema()
        schema_model_name = string.camel_case_to_snake_case(self._model.__class__.__name__)

        authentication = self.configuration("authentication")
        standard_error_responses = [
            self.documentation_input_error_response(),
        ]
        if not getattr(authentication, "is_public", False):
            standard_error_responses.append(self.documentation_access_denied_response())
            if getattr(authentication, "can_authorize", False):
                standard_error_responses.append(self.documentation_unauthorized_response())

        id_label = "id" if self.configuration("id_column_name") else self.id_column_name

        url = self.configuration("base_url")
        if include_id_in_path:
            url = url.rstrip("/") + "/{" + id_label + "}"

        return [
            autodoc.request.Request(
                description,
                [
                    self.documentation_success_response(
                        autodoc.schema.Object(
                            self.auto_case_internal_column_name("data"),
                            children=data_schema,
                            model_name=schema_model_name,
                        ),
                        description=description,
                    ),
                    *standard_error_responses,
                    self.documentation_not_found(),
                ],
                relative_path=url,
                parameters=[
                    *self.documentation_write_parameters(nice_model, include_id_in_path=include_id_in_path),
                ],
                root_properties={
                    "security": self.documentation_request_security(),
                },
            )
        ]

    def documentation_write_parameters(self, model_name, include_id_in_path=False):
        id_label = "id" if self.configuration("id_column_name") else self.id_column_name
        parameters = [
            autodoc.request.JSONBody(
                column.documentation(name=self.auto_case_column_name(column.name, True)),
                description=f"Set '{column.name}' for the {model_name}",
                required=column.is_required,
            )
            for column in self._get_writeable_columns().values()
        ]
        if include_id_in_path:
            parameters.append(
                autodoc.request.URLPath(
                    autodoc.schema.String(id_label),
                    description=f"The {id_label} of the record in question.",
                    required=True,
                )
            )
        return parameters
