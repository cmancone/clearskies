class Object:
    name = None
    children = None
    value = None
    _type = 'object'
    _format = ''

    def __init__(self, name, children, value=None):
        self.name = name
        self.children = children
        self.value = value
