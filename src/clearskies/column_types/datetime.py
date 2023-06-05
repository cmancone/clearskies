from .column import Column
from datetime import datetime, timezone
import dateparser
from ..autodoc.schema import DateTime as AutoDocDateTime
class DateTime(Column):
    _auto_doc_class = AutoDocDateTime

    def __init__(self, di):
        super().__init__(di)

    def from_backend(self, value):
        if not value or value == '0000-00-00 00:00:00':
            date = None
        elif type(value) == str:
            date = dateparser.parse(value)
        else:
            date = value
        return date.replace(tzinfo=timezone.utc) if date else None

    def to_backend(self, data):
        if not self.name in data or type(data[self.name]) == str or data[self.name] == None:
            return data

        # hopefully this is a Python datetime object in UTC timezone...
        return {**data, **{self.name: data[self.name].strftime('%Y-%m-%d %H:%M:%S')}}

    def to_json(self, model):
        datetime = model.get(self.name, silent=True)
        return datetime.isoformat() if datetime else None

    def build_condition(self, value, operator=None, column_prefix=''):
        date = dateparser.parse(value).astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        if not operator:
            operator = '='
        return f"{column_prefix}{self.name}{operator}{date}"

    def is_allowed_operator(self, operator, relationship_reference=None):
        """
        This is called when processing user data to decide if the end-user is specifying an allowed operator
        """
        return operator in ['=', '<', '>', '<=', '>=']

    def input_error_for_value(self, value, operator=None):
        value = dateparser.parse(value)
        if not value:
            return 'given value did not appear to be a valid date'
        if not value.tzinfo:
            return 'date is missing timezone information'
        return ''
