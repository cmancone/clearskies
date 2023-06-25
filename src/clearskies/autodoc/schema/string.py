class String:
    name = None
    example = None
    value = None
    _type = "string"
    _format = ""

    def __init__(self, name, example=None, value=None):
        self.name = name
        self.example = example
        self.value = value
