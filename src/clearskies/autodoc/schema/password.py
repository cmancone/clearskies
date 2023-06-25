from .string import String


class Password(String):
    _format = "password"

    def __init__(self, name, example=None, value=None):
        super().__init__(name, example=example, value=value)
