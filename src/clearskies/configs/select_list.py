from clearskies.configs import config


class SelectList(config.Config):
    """
    This is for a configuration that should be a list of strings matching some list of allowed values.

    The allowed values are set when you create the config, and when values are set for the config
    they must match.

    This is different than StringList, which also accepts a list of any strings.
    """

    def __init__(self, allowed_values: list[str], required=False, default=None):
        self.allowed_values = allowed_values
        self.required = required
        self.default = default

    def __set__(self, instance, value: list[str]):
        if value is None:
            return

        if not isinstance(value, list):
            error_prefix = self._error_prefix(instance)
            raise TypeError(
                f"{error_prefix} attempt to set a value of type '{value.__class__.__name__}' to a list parameter"
            )
        for index, item in enumerate(value):
            if not isinstance(item, str):
                error_prefix = self._error_prefix(instance)
                raise TypeError(
                    f"{error_prefix} attempt to set a value of type '{value.__class__.__name__}' for item #{index + 1}.  A string was expected."
                )

            if item not in self.allowed_values:
                error_prefix = self._error_prefix(instance)
                raise ValueError(
                    f"{error_prefix} attempt to set a value of '{item}' for item #{index + 1}.  This is not in the list of allowed values.  It must be one of '"
                    + "', '".join(self.allowed_values)
                    + "'"
                )
        instance._set_config(self, [*value])

    def __get__(self, instance, parent) -> list[str]:
        if not instance:
            return self  # type: ignore
        return instance._get_config(self)
