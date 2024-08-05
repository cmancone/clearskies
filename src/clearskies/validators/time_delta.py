from .requirement import Requirement
import datetime
from collections import OrderedDict


class TimeDelta(Requirement):
    time_delta = None

    def __init__(self, datetime):
        self.datetime = datetime

    def configure(self, time_delta: datetime.timedelta):
        if type(time_delta) != datetime.timedelta:
            raise ValueError(
                "The argument for all time-related input requirement classes is a datetime.timedelta object, but I received something else."
            )
        self.time_delta = time_delta
        self.human_friendly = None

    def delta_human_friendly(self):
        remainder = int(self.time_delta.total_seconds())
        parts = []
        conversion = OrderedDict(
            [
                ("year", 31536000),
                ("day", 86400),
                ("hour", 3600),
                ("minute", 60),
                ("second", 1),
            ]
        )
        for name, num_seconds in conversion.items():
            if num_seconds > remainder:
                continue
            amount = int(remainder / num_seconds)
            remainder -= amount * num_seconds
            parts.append(f"{amount} {name}" + ("s" if amount != 1 else ""))
        return ", ".join(parts)
