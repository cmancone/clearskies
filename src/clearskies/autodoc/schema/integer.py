class Integer:
    name = None
    example = None
    value = None
    _type = "integer"
    _format = "int32"

    def __init__(self, name, example=None, value=None):
        self.name = name
        self.example = example
        self.value = value
