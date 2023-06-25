from .string import String


class Base64(String):
    _format = "byte"

    def __init__(self, name, example=None, value=None):
        super().__init__(name, example=example, value=value)
