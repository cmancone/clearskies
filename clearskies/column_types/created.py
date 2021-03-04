from .datetime import DateTime


class Created(DateTime):
    @property
    def is_writeable(self):
        return False
