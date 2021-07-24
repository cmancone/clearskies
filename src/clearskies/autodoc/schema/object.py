class Object:
    name = None
    children = None
    value = None
    example = None
    model_name = None
    _type = 'object'
    _format = ''

    def __init__(self, name, children, value=None, example=None, model_name=None):
        self.name = name
        self.children = children
        self.value = value
        self.example = example
        self.model_name = model_name
