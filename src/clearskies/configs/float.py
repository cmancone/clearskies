from clearskies.configs import config


class Float(config.Config):
    def __set__(self, instance, value: float):
        if not isinstance(value, float):
            error_prefix = self._error_prefix(instance)
            raise TypeError(
                f"{error_prefix} attempt to set a value of type '{value.__class__.__name__}' to parameter that requires a float."
            )
        instance._set_config(self, value)

    def __get__(self, instance, parent) -> float:
        if not instance:
            return self  # type: ignore
        return instance._get_config(self)
