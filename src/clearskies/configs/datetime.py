import datetime

from clearskies.configs import config


class Datetime(config.Config):
    def __set__(self, instance, value: datetime.datetime):
        if not isinstance(value, datetime.datetime):
            error_prefix = self._error_prefix(instance)
            raise TypeError(
                f"{error_prefix} attempt to set a value of type '{value.__class__.__name__}' to a parameter that requries a datetime object."
            )
        instance._set_config(self, value)

    def __get__(self, instance, parent) -> datetime.datetime:
        if not instance:
            return self  # type: ignore
        return instance._get_config(self)
