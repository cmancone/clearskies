from .number import Number


class Double(Number):
    _format = "double"

    def __init__(self, name, example=None, value=None):
        super().__init__(name, example=example, value=value)
