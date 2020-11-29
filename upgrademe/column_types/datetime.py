from .column import Column
from datetime import datetime


class DateTime(Column):
    def from_database(self, value):
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S') if value else datetime.strptime('1-00-00', '%Y-%m-%d')

    def to_database(self, data):
        if not self.name in data or type(data[self.name]) == str:
            return data

        # hopefully this is a Python datetime object...
        return {
            **data,
            **{self.name: data[self.name].strftime('%Y-%m-%d %H:%M:%S')}
        }
