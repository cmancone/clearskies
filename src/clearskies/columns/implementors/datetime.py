from .column import Column
from datetime import datetime, timezone
import dateparser
from ..autodoc.schema import DateTime as AutoDocDateTime


class DateTime(Column):
    _auto_doc_class = AutoDocDateTime
    _date_format = "%Y-%m-%d %H:%M:%S"
    _default_date = "0000-00-00 00:00:00"

    my_configs = [
        "date_format",
        "default_date",
    ]

    def __init__(self, di, timezone: datetime.tzinfo):
        super().__init__(di)
        self._timezone = timezone

    def _finalize_configuration(self, configuration):
        return {
            **{
                "date_format": self._date_format,
                "default_date": self._default_date,
            },
            **super()._finalize_configuration(configuration),
        }

    def from_backend(self, value):
        if not value or value == self.config("default_date"):
            date = None
        elif type(value) == str:
            date = dateparser.parse(value)
        else:
            date = value
        return date.replace(tzinfo=self._timezone) if date else None

    def to_backend(self, data):
        if not self.name in data or type(data[self.name]) == str or data[self.name] == None:
            return data

        # hopefully this is a Python datetime object in UTC timezone...
        return {**data, **{self.name: data[self.name].strftime(self.config("date_format"))}}

    def to_json(self, model):
        datetime = model.get(self.name, silent=True)
        return {self.name: datetime.isoformat() if datetime else None}

    def build_condition(self, value, operator=None, column_prefix=""):
        date = dateparser.parse(value).astimezone(self._timezone).strftime(self.config("date_format"))
        if not operator:
            operator = "="
        return f"{column_prefix}{self.name}{operator}{date}"

    def is_allowed_operator(self, operator, relationship_reference=None):
        """
        This is called when processing user data to decide if the end-user is specifying an allowed operator
        """
        return operator in ["=", "<", ">", "<=", ">="]

    def input_error_for_value(self, value, operator=None):
        value = dateparser.parse(value)
        if not value:
            return "given value did not appear to be a valid date"
        if not value.tzinfo:
            return "date is missing timezone information"
        return ""

    def values_match(self, value_1, value_2):
        """
        Compares two values to see if they are the same
        """
        # in this function we deal with data directly out of the backend, so our date is likely
        # to be string-ified and we want to look for default (e.g. null) values in string form.
        if type(value_1) == str and "0000-00-00" in value_1:
            value_1 = None
        if type(value_2) == str and "0000-00-00" in value_2:
            value_2 = None
        number_values = 0
        if value_1:
            number_values += 1
        if value_2:
            number_values += 1
        if number_values == 0:
            return True
        if number_values == 1:
            return False

        if type(value_1) == str:
            value_1 = dateparser.parse(value_1)
        if type(value_2) == str:
            value_2 = dateparser.parse(value_2)

        # we need to make sure we're comparing in the same timezones.  For our purposes, a difference in timezone
        # is fine as long as they represent the same time (e.g. 16:00EST == 20:00UTC).  For python, same time in different
        # timezones is treated as different datetime objects.
        if value_1.tzinfo is not None and value_2.tzinfo is not None:
            value_1 = value_1.astimezone(value_2.tzinfo)

        # two times can be the same but if one is datetime-aware and one is not, python will treat them as not equal.
        # we want to treat such times as being the same.  Therefore, check for equality but ignore the timezone.
        for to_check in ["year", "month", "day", "hour", "minute", "second", "microsecond"]:
            if getattr(value_1, to_check) != getattr(value_2, to_check):
                return False

        # and since we already converted the timezones to match (or one has a timezone and one doesn't), we're good to go.
        # if we passed the above loop then the times are the same.
        return True
