from .string import String
class UUID(String):
    def __init__(self, uuid):
        self.uuid = uuid

    @property
    def is_writeable(self):
        return False

    def build_condition(self, value, operator=None):
        return f"{self.name}={value}"

    def is_allowed_operator(self, operator):
        """
        This is called when processing user data to decide if the end-user is specifying an allowed operator
        """
        return operator == '='

    def pre_save(self, data, model):
        if model.exists:
            return data
        return {**data, self.name: str(self.uuid.uuid4())}
