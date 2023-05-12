from collections import OrderedDict
from abc import ABC
from ..functional import validations
class FakeModel:
    def __getattr__(self, key):
        return None
class SchemaHelper(ABC):
    """
    A helper for handlers that want to accept arbitrary schemas as configuration inputs.

    To use this, the schema should be stored in a configuration called `schema`.  You can then check
    some data against the schema by doing something like this:

    ```
    input_errors = {
        **self._extra_column_errors(request_data),
        **self._find_input_errors(request_data),
    }
    ```
    """
    def _check_schema(self, schema, writeable_columns, error_prefix):
        """
        Validates that the schema provided in the configuration is valid.

        The schema is allowed to be one of 3 things:

        1. A list of column definitions.
        2. A model class.
        3. A model.

        An example of option #1 would be:

        ```
        {
            'schema': [
                clearskies.column_types.string('name', input_requirements=[clearskies.input_requirements.required()]),
                clearskies.column_types.integer('age'),
            ],
        }
        ```
        """
        is_valid_schema = False
        if validations.is_model_or_class(schema):
            is_valid_schema = True
        else:
            if not hasattr(schema, '__iter__') or type(schema) == str:
                raise ValueError(
                    f"{error_prefix} 'schema' should be a list of column definitions, but was instead a " +
                    type(schema)
                )
            for column in schema:
                if type(column) != tuple:
                    raise ValueError(
                        f"{error_prefix} 'schema' should be a list of column definitions, but one of the entries was not a column definition"
                    )
            is_valid_schema = True
        if not is_valid_schema:
            raise ValueError(
                f"{error_prefix} 'schema' should be a model, model class, or list of column definitions, but was instead a "
                + type(schema)
            )

        if not writeable_columns and writeable_columns is not None:
            raise ValueError(
                f"{error_prefix} 'writeable_columns' can't be an empty list.  It can be 'None', but otherwise I don't know how to handle empty values"
            )

        if writeable_columns:
            if not hasattr(writeable_columns, '__iter__') or type(writeable_columns) == str:
                raise ValueError(
                    f"{error_prefix} 'writeable_columns' should be a list of column names, but was instead a " +
                    type(writeable_columns)
                )
            columns = self._schema_to_columns(schema)
            for column in writeable_columns:
                if type(column) != str:
                    raise ValueError(
                        f"{error_prefix} 'writeable_columns' should be a list of column names, but one of the entries was not a string"
                    )
                if column not in columns:
                    raise ValueError(
                        f"{error_prefix} 'writeable_columns' references a column named '{column}' but this column does not exist in the schema"
                    )

    def _schema_to_columns(self, schema, columns_to_keep=None):
        """
        Converts the schema from the developer to a columns object
        """
        # the schema can be a model, model class, or list of column configs.
        # Each requires a different conversion method
        if validations.is_model(schema):
            columns = schema.columns()
        elif validations.is_model_class(schema):
            columns = self._di.build(schema).columns()
        else:
            columns = self._di.build('columns').configure(OrderedDict(schema), self.__class__)

        # if we don't have a list of columns to keep, then we're done
        if not columns_to_keep:
            return columns

        # only keep things that we're allowed to keep
        return OrderedDict([(key, value) for (key, value) in columns.items() if key in columns_to_keep])

    def _find_input_errors(self, input_data, schema=None):
        if not schema:
            schema = self.configuration('schema')
        input_errors = {}
        fake_model = FakeModel()
        for column in schema.values():
            input_errors = {
                **input_errors,
                **column.input_errors(fake_model, input_data),
            }
        return input_errors

    def _extra_column_errors(self, input_data, schema=None):
        if not schema:
            schema = self.configuration('schema')
        input_errors = {}
        for column_name in input_data.keys():
            if column_name not in schema:
                input_errors[column_name] = f"Input column '{column_name}' is not an allowed column"
        return input_errors
