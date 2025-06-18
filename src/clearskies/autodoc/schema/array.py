from .schema import Schema


class Array(Schema):
    item_definition = None
    _type = "array"

    def __init__(self, name, item_definition, value=None):
        super().__init__(name, example=None, value=value)
        self.item_definition = item_definition
