import datetime

from clearskies.configs import config


class Timezone(config.Config):
    def __set__(self, instance, value: datetime.timezone | None):
        if value and not isinstance(value, datetime.timezone):
            error_prefix = self._error_prefix(instance)
            raise TypeError(
                f"{error_prefix} attempt to set a value of type '{value.__class__.__name__}' to a parameter that requries a timezone (datetime.timezone)."
            )
        instance._set_config(self, value)

    def __get__(self, instance, parent) -> datetime.timezone:
        if not instance:
            return self  # type: ignore
        return instance._get_config(self)
