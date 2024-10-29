from typing import List

from clearskies.configs import string


class SelectList(string.String):
    def __init__(self, allowed_values: List[str], required=False, default=None):
        self.allowed_values = allowed_values

    def __set__(self, instance, value: List[str]):
        if value is None:
            return

        if not isinstance(value, list):
            error_prefix = self._error_prefix(instance)
            raise TypeError(
                f"{error_prefix} attempt to set a value of type '{value.__class__.__name__}' to a list parameter"
            )
        for item in value:
            if not isinstance(item, str):

            if value not in self.allowed_values:
                raise ValueError(
                    f"{error_prefix} attempt to set a value of type '{value}' which is not in the list of allowed values.  It must be one of '"
                    + "', '".join(self.allowed_values)
                    + "'"
                )
        instance._set_config(self, value)
