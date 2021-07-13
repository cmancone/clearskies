from .column import Column
from datetime import datetime, timezone
import dateparser


class DateTime(Column):
    response_schema_type = 'string'
    response_schema_format = 'date-time'

    def from_database(self, value):
        if value == None:
            date = datetime.strptime('1970-01-01', '%Y-%m-%d')
        elif type(value) == str:
            date = datetime.strptime(value, '%Y-%m-%d %H:%M:%S') if value else datetime.strptime('1970-01-01', '%Y-%m-%d')
        else:
            date = value
        return date.replace(tzinfo=timezone.utc)

    def to_database(self, data):
        if not self.name in data or type(data[self.name]) == str:
            return data

        # hopefully this is a Python datetime object in UTC timezone...
        return {
            **data,
            **{self.name: data[self.name].strftime('%Y-%m-%d %H:%M:%S')}
        }

    def to_json(self, model):
        return model.__getattr__(self.name).isoformat()

    def build_condition(self, value, operator=None):
        date = dateparser.parse(value).astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        if not operator:
            operator = '='
        return f"{self.name}{operator}{date}"

    def is_allowed_operator(self, operator):
        """
        This is called when processing user data to decide if the end-user is specifying an allowed operator
        """
        return operator in ['=', '<', '>', '<=', '>=']

    def input_error_for_value(self, value):
        value = dateparser.parse(value)
        if not value:
            return 'given value did not appear to be a valid date'
        if not value.tzinfo:
            return 'date is missing timezone information'
        return ''
