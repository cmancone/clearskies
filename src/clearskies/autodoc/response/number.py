class Number:
    name = None
    example = None
    value = None
    _type = 'number'
    _format = 'float'

    def __init__(self, name, example=None, value=None):
        self.name = name
        self.example = example
        self.value = value
