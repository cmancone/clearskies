from .string import String


class CreatedByAuthorizationData(String):
    required_configs = [
        "authorization_data_key_name",
    ]

    def __init__(self, di):
        super().__init__(di)

    @property
    def is_writeable(self):
        return False

    def pre_save(self, data, model):
        if model.exists:
            return data

        authorization_data = self.di.build("input_output", cache=True).get_authorization_data()
        return {**data, self.name: authorization_data.get(self.config("authorization_data_key_name"), "N/A")}
