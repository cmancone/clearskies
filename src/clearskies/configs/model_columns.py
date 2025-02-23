from clearskies.configs import select_list


class ModelColumns(select_list.SelectList):
    def __init__(self, model_column_config_name="", allow_relationship_references=False, required=False, default=None):
        self.required = required
        self.default = default
        self.model_column_config_name = model_column_config_name
        self.allow_relationship_references = allow_relationship_references

    def __set__(self, instance, value: list[str]):
        if value is None:
            return

        if not isinstance(value, list):
            error_prefix = self._error_prefix(instance)
            raise TypeError(
                f"{error_prefix} attempt to set a value of type '{value.__class__.__name__}' to a list parameter"
            )

        instance._set_config(self, value)
        # unlike select_list, we won't validate the value currently because we won't be able to
        # do that until the finalize_and_validate_configuration phase

    def get_allowed_columns(self, model_class, column_configs):
        return [name for name in column_configs.keys()]

    def my_description(self):
        return "column"

    def finalize_and_validate_configuration(self, instance):
        super().finalize_and_validate_configuration(instance)

        # when we were created we were told the name of the config that stores
        # the model class we're getting readable columns from.  Let's use that
        # and fetch the model class.  Note that this is an optional feature though
        if not self.model_column_config_name:
            return

        model_class = getattr(instance, self.model_column_config_name)
        values = instance._get_config(self)
        if not values or not model_class:
            return

        allowed_columns = self.get_allowed_columns(model_class, model_class.get_columns())
        for value in values:
            if self.allow_relationship_references and "." in value:
                value = value.split(".")[0]
            if value not in allowed_columns:
                error_prefix = self._error_prefix(instance)
                my_description = self.my_description()
                raise ValueError(
                    f"{error_prefix} attempt to set a value of '{value}' but this is not a {my_description} in the specified model class, '{model_class.__name__}.  Expected values are: '"
                    + "', '".join(allowed_columns)
                    + "'"
                )
