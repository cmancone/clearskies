from .binding import Binding


class Action(Binding):
    def __init__(self, action_class, *args, **kwargs):
        return super().__init__(action_class, *args, **kwargs)
