from .datetime import DateTime


class Updated(DateTime):
    my_configs = [
        "date_format",
        "default_date",
        "utc",
    ]

    def __init__(self, di, datetime):
        super().__init__(di)
        self.datetime = datetime

    @property
    def is_writeable(self):
        return False

    def pre_save(self, data, model):
        if self.config("utc", silent=True):
            now = self.datetime.datetime.now(self.datetime.timezone.utc)
        else:
            now = self.datetime.datetime.now()
        return {**data, self.name: now}
