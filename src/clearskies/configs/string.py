from clearskies.configs import config


class String(config.Config):
    def __set__(self, instance, value: str):
        if not isinstance(value, str):
            error_prefix = self._error_prefix(instance)
            raise TypeError(
                f"{error_prefix} attempt to set a value of type '{value.__class__.__name__}' to a parameter that requires a string."
            )
        instance._set_config(self, value)

    def __get__(self, instance, parent) -> str:
        if not instance:
            return self  # type: ignore
        return instance._get_config(self)
