from re import T
from .datetime import DateTime
from datetime import datetime, timezone
import dateparser
from ..autodoc.schema import DateTime as AutoDocDateTime


class DateTimeMicro(DateTime):
    _date_format = "%Y-%m-%d %H:%M:%S.%f"
    _default_date = "0000-00-00 00:00:00.000000"

    def __init__(self, di, timezone: datetime.tzinfo):
        super().__init__(di, timezone)
