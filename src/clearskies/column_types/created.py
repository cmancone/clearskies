from .datetime import DateTime


class Created(DateTime):
    def __init__(self, now):
        self.now = now

    @property
    def is_writeable(self):
        return False

    def pre_save(self, data, model):
        if model.exists:
            return data
        return {
            **data,
            self.name: self.now
        }
