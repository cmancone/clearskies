from clearskies.configs import config


class StringDict(config.Config):
    """This is for a configuration that should be a dictionary with keys and values that are all strings."""

    def __set__(self, instance, value: dict[str, str]):
        if value is None:
            return

        if not isinstance(value, dict):
            error_prefix = self._error_prefix(instance)
            raise TypeError(
                f"{error_prefix} attempt to set a value of type '{value.__class__.__name__}' to a dict parameter"
            )
        for key, val in value.items():
            if not isinstance(key, str):
                error_prefix = self._error_prefix(instance)
                raise TypeError(
                    f"{error_prefix} attempt to set a key of type '{key.__class__.__name__}' when only string keys are allowed."
                )
            if not isinstance(val, str):
                error_prefix = self._error_prefix(instance)
                raise TypeError(
                    f"{error_prefix} attempt to set a value of type '{val.__class__.__name__}' for key '{key}'.  A string was expected."
                )
        instance._set_config(self, value)

    def __get__(self, instance, parent) -> dict[str, str]:
        if not instance:
            return self  # type: ignore
        return instance._get_config(self)
