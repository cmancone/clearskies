from .string import String


class UUID(String):
    def __init__(self, di, uuid):
        super().__init__(di)
        self.uuid = uuid

    @property
    def is_writeable(self):
        return False

    def build_condition(self, value, operator=None, column_prefix=""):
        return f"{column_prefix}{self.name}={value}"

    def is_allowed_operator(self, operator, relationship_reference=None):
        """
        This is called when processing user data to decide if the end-user is specifying an allowed operator
        """
        return operator == "="

    def pre_save(self, data, model):
        if model.exists:
            return data
        return {**data, self.name: str(self.uuid.uuid4())}
