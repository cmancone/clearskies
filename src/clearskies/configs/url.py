from clearskies.configs import string
from clearskies.functional import routing


class Url(string.String):
    def __set__(self, instance, value: str):
        if value is None:
            return

        if not isinstance(value, str):
            error_prefix = self._error_prefix(instance)
            raise TypeError(
                f"{error_prefix} attempt to set a value of type '{value.__class__.__name__}' to a url parameter"
            )
        value = value.strip("/")

        if value:
            try:
                routing.extract_url_parameter_name_map(value)
            except ValueError as e:
                error_prefix = self._error_prefix(instance)
                raise ValueError(f"{error_prefix} {e}")
        instance._set_config(self, value)
