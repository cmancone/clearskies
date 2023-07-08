import json
from .column import Column


class JSON(Column):
    def __init__(self, di):
        super().__init__(di)

    def from_backend(self, value):
        if type(value) == list or type(value) == dict:
            return value
        if not value:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None

    def to_backend(self, data):
        if self.name in data:
            data[self.name] = json.dumps(data[self.name]) if data[self.name] else ""
        return data

    def to_json(self, model):
        return {self.name: model.get(self.name, silent=True)}
