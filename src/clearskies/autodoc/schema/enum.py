class Enum:
    name = None
    values = None
    value_type = None
    example = None
    _type = "string"
    _format = ""

    def __init__(self, name, values, value_type, example=None):
        self.name = name
        self.values = values
        self.value_type = value_type
        self._type = value_type._type
        self._format = value_type._format
        self.example = example
