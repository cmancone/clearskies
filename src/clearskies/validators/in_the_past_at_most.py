from clearskies.validators.timedelta import Timedelta
import datetime


class InThePastAtMost(Timedelta):
    def check_timedelta(self, as_date: datetime.timedelta, column_name: str) -> str:
        if as_date < self.utcnow - self.timedelta:
            return f"'{column_name}' must be at most {self.delta_human_friendly()} in the past."
        return ""
