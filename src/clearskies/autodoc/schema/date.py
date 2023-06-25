from .string import String


class Date(String):
    _format = "date"

    def __init__(self, name, example=None, value=None):
        super().__init__(name, example=example, value=value)
