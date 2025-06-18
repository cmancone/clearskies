from clearskies.configs import string


class Select(string.String):
    def __init__(self, allowed_values: list[str], required=False, default=None):
        self.allowed_values = allowed_values
        self.required = required
        self.default = default

    def __set__(self, instance, value: str):
        if value is None:
            return

        if not isinstance(value, str):
            error_prefix = self._error_prefix(instance)
            raise TypeError(
                f"{error_prefix} attempt to set a value of type '{value.__class__.__name__}' to a string parameter"
            )
        if value not in self.allowed_values:
            error_prefix = self._error_prefix(instance)
            raise ValueError(
                f"{error_prefix} attempt to set a value of type '{value}' which is not in the list of allowed values.  It must be one of '"  # type: ignore
                + "', '".join(self.allowed_values)
                + "'"
            )
        instance._set_config(self, value)
