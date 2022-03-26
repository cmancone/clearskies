from .integer import Integer
class Long(Integer):
    _format = 'int64'

    def __init__(self, name, example=None, value=None):
        super().__init__(name, example=example, value=value)
