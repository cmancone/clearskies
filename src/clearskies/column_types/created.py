from .datetime import DateTime


class Created(DateTime):
    my_configs = [
        "date_format",
        "default_date",
        "utc",
    ]

    def __init__(self, di, datetime, timezone):
        super().__init__(di, timezone)
        self.datetime = datetime

    @property
    def is_writeable(self):
        return False

    def pre_save(self, data, model):
        if model.exists:
            return data
        if self.config("utc", silent=True):
            now = self.datetime.datetime.now(self.datetime.timezone.utc)
        else:
            now = self.datetime.datetime.now(self._timezone)
        return {**data, self.name: now}
