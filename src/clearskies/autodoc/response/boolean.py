class Boolean:
    name = None
    example = None
    value = None
    _type = 'boolean'
    _format = ''

    def __init__(self, name, example=None, value=None):
        self.name = name
        self.example = example
        self.value = value
