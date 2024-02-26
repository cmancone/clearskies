from .time_delta import TimeDelta
import datetime
import dateparser


class InTheFutureAtMost(TimeDelta):
    def check(self, model, data):
        if self.column_name not in data or not data[self.column_name]:
            return ""
        as_date = dateparser.parse(data[self.column_name])
        if not as_date:
            return f"'{self.column_name}' was not a valid date"
        now = (
            self.datetime.datetime.now() if not as_date.tzinfo else self.datetime.datetime.now(tz=datetime.timezone.utc)
        )
        if as_date > now + self.time_delta:
            human_friendly = self.delta_human_friendly()
            return f"'{self.column_name}' must be at most {human_friendly} in the future."
        return ""
