import datetime

from clearskies.validators.timedelta import Timedelta


class InThePastAtLeast(Timedelta):
    def check_timedelta(self, as_date: datetime.datetime, column_name: str) -> str:
        if as_date > self.utcnow - self.timedelta:
            return f"'{column_name}' must be at least {self.delta_human_friendly()} in the past."
        return ""
