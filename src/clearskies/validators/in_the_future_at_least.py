import datetime

from clearskies.validators.timedelta import Timedelta


class InTheFutureAtLeast(Timedelta):
    def check_timedelta(self, as_date: datetime.datetime, column_name: str) -> str:
        if as_date < self.utcnow + self.timedelta:
            human_friendly = self.delta_human_friendly()
            return f"'{column_name}' must be at least {human_friendly} in the future."
        return ""
