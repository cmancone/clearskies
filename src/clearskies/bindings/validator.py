from .binding import Binding


class Validator(Binding):
    def __init__(self, validator_class, *args, **kwargs):
        return super().__init__(validator_class, *args, **kwargs)
