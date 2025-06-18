import datetime

from clearskies.validators.after_column import AfterColumn


class BeforeColumn(AfterColumn):
    def date_comparison(self, incoming_date: datetime.datetime, comparison_date: datetime.datetime, column_name) -> str:
        if incoming_date == comparison_date:
            return "" if self.allow_equal else f"'{column_name}' must be before '{self.other_column_name}'"

        if incoming_date > comparison_date:
            return f"'{column_name}' must be before '{self.other_column_name}'"
        return ""
