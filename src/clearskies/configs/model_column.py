from clearskies.configs import select


class ModelColumn(select.Select):
    def __init__(self, model_column_config_name="", required=False, default=None):
        self.required = required
        self.default = default
        self.model_column_config_name = model_column_config_name
        self.model_class = None

    def __set__(self, instance, value: str):
        if value is None:
            return

        if not isinstance(value, str):
            error_prefix = self._error_prefix(instance)
            raise TypeError(
                f"{error_prefix} attempt to set a value of type '{value.__class__.__name__}' to a string parameter"
            )

        instance._set_config(self, value)
        # unlike select, we won't validate the value currently because we won't be able to
        # do that until the finalize_and_validate_configuration phase

    def get_allowed_columns(self, model_class, column_configs):
        return [name for name in column_configs.keys()]

    def my_description(self):
        return "column"

    def get_model_class(self, instance):
        model_class = self.model_class
        if not model_class and self.model_column_config_name:
            model_class = getattr(instance, self.model_column_config_name)
        return model_class

    def set_model_class(self, model_class):
        self.model_class = model_class

    def finalize_and_validate_configuration(self, instance):
        super().finalize_and_validate_configuration(instance)

        # to check for a valid column we need to know the name of the model class.
        # This can be either provided to us directly or we may be given the name of a configuration
        # from which we fetch the model class
        model_class = self.get_model_class(instance)

        # if we don't have one though, no worries - some classes have to provide it later and
        # can trigger validation then.
        if not model_class:
            return

        allowed_columns = self.get_allowed_columns(model_class, model_class.get_columns())

        value = instance._get_config(self)
        if not value:
            return
        if value not in allowed_columns:
            error_prefix = self._error_prefix(instance)
            my_description = self.my_description()
            raise ValueError(
                f"{error_prefix} attempt to set a value of '{value}' but this is not a {my_description} in the specified model class, '{model_class.__name__}'.  Expected values are: '"
                + "', '".join(allowed_columns)
                + "'"
            )
