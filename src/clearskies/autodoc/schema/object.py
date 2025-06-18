from .schema import Schema


class Object(Schema):
    children = None
    model_name = None
    _type = "object"
    _format = ""

    def __init__(self, name, children, value=None, example=None, model_name=None):
        super().__init__(name, example=example, value=value)
        self.children = children
        self.model_name = model_name
