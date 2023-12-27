from .datetime_micro import DateTimeMicro


class UpdatedMicro(DateTimeMicro):
    def __init__(self, di, now):
        super().__init__(di)
        self.now = now

    @property
    def is_writeable(self):
        return False

    def pre_save(self, data, model):
        return {**data, self.name: self.now}
