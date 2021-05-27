import json
from .column import Column


class JSON(Column):
    def from_database(self, value):
        if type(value) == list or type(value) == dict:
            return value
        return json.loads(value) if value else {}

    def to_database(self, data):
        if self.name in data:
            data[self.name] = json.dumps(data[self.name]) if data[self.name] else {}
        return data
