class Array:
    name = None
    value = None
    item_definition = None
    _type = "array"
    _format = ""

    def __init__(self, name, item_definition, value=None):
        self.name = name
        self.value = value
        self.item_definition = item_definition
