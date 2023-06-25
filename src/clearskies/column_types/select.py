from .string import String


class Select(String):
    required_configs = ["values"]

    def __init__(self, di):
        super().__init__(di)

    def input_error_for_value(self, value, operator=None):
        return f"Invalid value for {self.name}" if value not in self.config("values") else ""
