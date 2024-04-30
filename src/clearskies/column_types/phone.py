from .string import String
import re


class Phone(String):
    my_configs = [
        "usa_only",
    ]

    def __init__(self, di):
        super().__init__(di)

    def to_backend(self, data):
        if self.name not in data:
            return data

        # phone numbers are stored as only digits.
        return {**data, **{self.name: re.sub(r"\D", "", data[self.name])}}

    def input_error_for_value(self, value, operator=None):
        if type(value) != str:
            return f"Value must be a string for {self.name}"

        # we'll allow spaces, dashes, parenthesis, dashes, and plus signs.
        # if there is anything else then it's not a valid phone number.
        # However, we don't do more detailed validation, because I'm too lazy to
        # figure out what is and is not a valid phone number, especially when
        # you get to the world of international numbers.
        if re.search(r"[^\d \-()+]", value):
            return "Invalid phone number"

        # for some final validation (especially US numbers) work only with the digits.
        value = re.sub(r"\D", "", value)

        if len(value) > 15:
            return "Invalid phone number"

        # we can't be too short unless we're doing a fuzzy search
        if len(value) < 10 and operator and operator.lower() != "like":
            return "Invalid phone number"

        if self.config("usa_only", silent=True):
            if len(value) > 11:
                return "Invalid phone number"
            if value[0] == "1" and len(value) != 11:
                return "Invalid phone number"

        return ""
