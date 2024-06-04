import datetime

from .datetime_micro import DateTimeMicro


class UpdatedMicro(DateTimeMicro):
    my_configs = [
        "date_format",
        "default_date",
        "utc",
    ]

    def __init__(self, di, datetime, timezone: datetime.tzinfo):
        super().__init__(di, timezone)
        self.datetime = datetime

    @property
    def is_writeable(self):
        return False

    def pre_save(self, data, model):
        if self.config("utc", silent=True):
            now = self.datetime.datetime.now(self.datetime.timezone.utc)
        else:
            now = self.datetime.datetime.now(self._timezone)
        return {**data, self.name: now}
