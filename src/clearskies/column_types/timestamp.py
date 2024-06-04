import time
from .datetime import DateTime
from datetime import datetime, timezone
import dateparser
from ..autodoc.schema import DateTime as AutoDocDateTime


class Timestamp(DateTime):
    my_configs = [
        "date_format",
        "milliseconds",
    ]

    def _finalize_configuration(self, configuration):
        return {
            **{
                "date_format": self._date_format,
                "milliseconds": False,
            },
            **super()._finalize_configuration(configuration),
        }

    def from_backend(self, value):
        mult = 1000 if self.config("milliseconds") else 1
        if not value:
            date = None
        elif isinstance(value, str):
            if not value.isdigit():
                raise ValueError(
                    f"Invalid data was found in the backend for model {self.model_class.__name__} and column {self.name}: a string value was found that is not a timestamp.  It was '{value}'"
                )
            date = datetime.fromtimestamp(int(value) / mult, self._timezone)
        elif isinstance(value, int):
            date = datetime.fromtimestamp(value / mult, self._timezone)
        else:
            if not isinstance(value, datetime):
                raise ValueError(
                    f"Invalid data was found in the backend for model {self.model_class.__name__} and column {self.name}: the value was neither an integer, a string, nor a datetime object"
                )
            date = value
        return date.replace(tzinfo=self._timezone) if date else None

    def to_backend(self, data):
        if not self.name in data or isinstance(data[self.name], int) or data[self.name] == None:
            return data

        value = data[self.name]
        if isinstance(value, str):
            if not value.isdigit():
                raise ValueError(
                    f"Invalid data was sent to the backend for model {self.model_class.__name__} and column {self.name}: a string value was found that is not a timestamp. It was '{value}'"
                )
            value = int(value)
        elif isinstance(value, datetime):
            value = value.timestamp()
        else:
            raise ValueError(
                f"Invalid data was sent to the backend for model {self.model_class.__name__} and column {self.name}: the value was neither an integer, a string, nor a datetime object"
            )

        # hopefully this is a Python datetime object in UTC timezone...
        return {**data, **{self.name: value}}

    def input_error_for_value(self, value, operator=None):
        if not isinstance(value, int):
            return f"'{self.name}' must be an integer"
        return ""

    def values_match(self, value_1, value_2):
        """
        Compares two values to see if they are the same
        """
        return value_1 == value_2
