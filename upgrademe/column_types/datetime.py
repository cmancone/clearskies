from .column import Column
from datetime import datetime, timezone


class DateTime(Column):
    def from_database(self, value):
        date = datetime.strptime(value, '%Y-%m-%d %H:%M:%S') if value else datetime.strptime('1-00-00', '%Y-%m-%d')
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
