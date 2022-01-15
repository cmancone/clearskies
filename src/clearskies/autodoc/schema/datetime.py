from .string import String
class DateTime(String):
    _format = 'date-time'

    def __init__(self, name, example=None, value=None):
        super().__init__(name, example=example, value=value)
